import os
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceInferenceAPIEmbeddings
from .guardrails import Guardrails
from .search import Searcher
from .augmenter import Augmenter

class QueryProcessor:
    def __init__(self):
        # 1. Initialize Core Engines
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")
            
        self.llm = ChatGroq(
            temperature=0.1,
            model_name="llama-3.1-8b-instant",
            groq_api_key=groq_api_key
        )
        
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not hf_token:
            raise ValueError("HUGGINGFACEHUB_API_TOKEN not found in environment.")

        embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=hf_token,
            model_name="BAAI/bge-small-en-v1.5"
        )

        # 2. Initialize Sub-Modules
        self.guardrails = Guardrails(self.llm)
        self.searcher = Searcher(embeddings)
        self.augmenter = Augmenter(self.llm)

    def get_answer(self, user_query: str) -> str:
        # 0. Basic Keyword Check
        advisory_keywords = ["better", "best", "should i", "recommend", "compare", "which factor", "is it good"]
        if any(word in user_query.lower() for word in advisory_keywords):
             return ("I am an objective assistant and cannot provide investment advice, relative comparisons, or specific recommendations.")

        # 1. PII Scrubbing
        sanitized_query = self.guardrails.scrub_pii(user_query)
        if "REDACTED" in sanitized_query:
            return "I'm sorry, I cannot process queries containing personal identifiers like PAN or Aadhaar."

        # 2. Intent Check
        if not self.guardrails.is_factual_intent(sanitized_query):
            return "I am an objective assistant and cannot provide investment advice or specific recommendations."

        # 3. Retrieval
        context, metadata = self.searcher.find_relevant_context(sanitized_query)
        if not context:
            return "I'm sorry, I couldn't find any factual information regarding that query in the official documents."

        # 4. Augmentation & Generation
        response = self.augmenter.generate_response(sanitized_query, context)
        
        return response
