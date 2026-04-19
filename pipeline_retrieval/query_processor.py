import os
import re
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb

# Load environment variables
load_dotenv()

class QueryProcessor:
    def __init__(self):
        # 1. Initialize LLM (Groq Llama 3)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")
        
        self.llm = ChatGroq(
            temperature=0.1, # Low temperature for factual accuracy
            model_name="llama-3.1-8b-instant",
            groq_api_key=self.groq_api_key
        )

        # 2. Initialize Embeddings (same model as ingestion)
        model_name = "BAAI/bge-small-en-v1.5"
        encode_kwargs = {'normalize_embeddings': True}
        model_kwargs = {'device': 'cpu'}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs=encode_kwargs,
            model_kwargs=model_kwargs
        )

        # 3. Initialize Chroma Client
        self.chroma_host = os.getenv("CHROMA_HOST", "api.trychroma.com")
        if not self.chroma_host.startswith("http"):
            self.chroma_host = f"https://{self.chroma_host}"
            
        self.chroma_api_key = os.getenv("CHROMA_API_KEY")
        self.chroma_database = os.getenv("CHROMA_DATABASE", "RAG_chatbot_database")
        self.chroma_tenant = os.getenv("CHROMA_TENANT", "55f74872-3fe6-4e35-ab34-fd70ca9022fc")

        self.chroma_client = chromadb.HttpClient(
            host=self.chroma_host,
            headers={"x-chroma-token": self.chroma_api_key},
            tenant=self.chroma_tenant,
            database=self.chroma_database,
            ssl=True
        )

        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name="mutual_fund_faqs",
            embedding_function=self.embeddings
        )

    def scrub_pii(self, query: str) -> str:
        """Removes potential PII like PAN and Aadhaar from the query."""
        # Generic Regex for PAN (5 letters, 4 digits, 1 letter)
        pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
        # Generic Regex for Aadhaar (12 digits)
        aadhaar_pattern = r'\b[0-9]{12}\b'
        # Generic Email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        query = re.sub(pan_pattern, "[REDACTED_ID]", query, flags=re.IGNORECASE)
        query = re.sub(aadhaar_pattern, "[REDACTED_ID]", query)
        query = re.sub(email_pattern, "[REDACTED_EMAIL]", query)
        
        return query

    def classify_intent(self, query: str) -> bool:
        """
        Returns True if the query is factual.
        Returns False if the query seeks investment advice or is subjective.
        """
        prompt = f"""You are a security guard for a Mutual Fund FAQ assistant. 
        Analyze the user query: "{query}"
        Does this query ask for:
        1. Investment advice or specific recommendations? ("Should I buy?", "Is this good?")
        2. Relative comparisons or qualitative evaluations? ("Which is better?", "Which is safer?", "Is A better than B?")
        3. Performance predictions or opinions?
        4. Personal account private data?

        If it asks for ANY of the above, reply with "ADVICE".
        If it asks for ONLY OBJECTIVE FACTS found in a factsheet (expense ratio, exit load, SIP amount, lock-in, benchmark), reply with "FACTUAL".
        
        Response (one word only):"""
        
        response = self.llm.invoke(prompt).content.strip().upper()
        return "FACTUAL" in response

    def get_answer(self, user_query: str) -> str:
        # 0. Basic Advisory Keywords (Hard Override for compliance)
        advisory_keywords = ["better", "best", "should i", "recommend", "compare", "which factor", "is it good"]
        if any(word in user_query.lower() for word in advisory_keywords):
             return ("I am an objective assistant and cannot provide investment advice, relative comparisons, or specific recommendations. "
                    "For financial planning, please consult a certified advisor or refer to official [AMFI](https://www.amfiindia.com) resources.")

        # 1. Scrub PII
        sanitized_query = self.scrub_pii(user_query)
        if "REDACTED" in sanitized_query:
            return "I'm sorry, I cannot process queries containing personal identifiers like PAN or Aadhaar. Please remove them and try again."

        # 2. Classify Intent
        is_factual = self.classify_intent(sanitized_query)
        if not is_factual:
            return ("I am an objective assistant and cannot provide investment advice, relative comparisons, or specific recommendations. "
                    "For financial planning, please consult a certified advisor or refer to official [AMFI](https://www.amfiindia.com) resources.")

        # 3. Retrieve Context
        results = self.vectorstore.similarity_search(sanitized_query, k=3)
        if not results:
            return "I'm sorry, I couldn't find any factual information regarding that query in the official HDFC fund documents provided."

        context = "\n---\n".join([doc.page_content for doc in results])
        # Find the primary source link from the top result
        source_link = results[0].metadata.get("source_url", "https://groww.in")
        extraction_date = results[0].metadata.get("extraction_date", "recent")

        # 4. Generate Response
        system_prompt = f"""You are a factual Mutual Fund FAQ Assistant. 
        Use ONLY the provided context below to answer the user's question.
        Guidelines:
        - Max 3 sentences.
        - Be objective and technical.
        - Do NOT offer advice.
        - Do NOT include disclaimers about data being as of a specific date or AUM changes.
        - If the answer isn't in the context, say you don't know based on official factsheets.

        Context:
        {context}

        Question: {sanitized_query}
        """

        response = self.llm.invoke(system_prompt).content.strip()

        # 5. Format Output (Simplified as per request)
        return response

if __name__ == "__main__":
    # Quick test
    processor = QueryProcessor()
    test_query = "What is the exit load for HDFC Mid-Cap fund?"
    print(f"Query: {test_query}")
    print(processor.get_answer(test_query))
