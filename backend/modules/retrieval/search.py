import os
import chromadb

class Searcher:
    def __init__(self, embedding_function):
        # Configuration
        self.host = os.environ.get("CHROMA_HOST", "api.chromadb.com")
        if not self.host.startswith("http"):
            self.host = f"https://{self.host}"
            
        self.api_key = os.environ.get("CHROMA_API_KEY", "")
        self.database = os.environ.get("CHROMA_DATABASE", "RAG_chatbot_database")
        self.tenant = os.environ.get("CHROMA_TENANT", "55f74872-3fe6-4e35-ab34-fd70ca9022fc")
        
        self.embedding_function = embedding_function

        # Initialize Client
        self.chroma_client = chromadb.HttpClient(
            host=self.host,
            headers={"x-chroma-token": self.api_key},
            tenant=self.tenant,
            database=self.database,
            ssl=True
        )

        self.collection = self.chroma_client.get_collection(name="mutual_fund_faqs")

    def find_relevant_context(self, query: str, k=3):
        """Retrieves top-k relevant chunks using the Chroma SDK directly."""
        # Generate query vector using our weightless client
        query_vector = self.embedding_function.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            include=["documents", "metadatas"]
        )
        
        if not results or not results["documents"] or not results["documents"][0]:
            return None, None
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        
        context = "\n---\n".join(documents)
        metadata = {
            "source_url": metadatas[0].get("source_url", "https://groww.in"),
            "extraction_date": metadatas[0].get("extraction_date", "recent")
        }
        return context, metadata
