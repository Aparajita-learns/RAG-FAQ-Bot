import os
import chromadb
from langchain_chroma import Chroma

class Searcher:
    def __init__(self, embedding_function):
        # Configuration
        host = os.environ.get("CHROMA_HOST", "https://api.trychroma.com")
        if not host.startswith("http"):
            host = f"https://{host}"
            
        api_key = os.environ.get("CHROMA_API_KEY", "")
        database = os.environ.get("CHROMA_DATABASE", "RAG_chatbot_database")
        tenant = os.environ.get("CHROMA_TENANT", "55f74872-3fe6-4e35-ab34-fd70ca9022fc")

        # Initialize Client
        self.chroma_client = chromadb.HttpClient(
            host=host,
            headers={"x-chroma-token": api_key},
            tenant=tenant,
            database=database,
            ssl=True
        )

        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name="mutual_fund_faqs",
            embedding_function=embedding_function
        )

    def find_relevant_context(self, query: str, k=3):
        """Retrieves top-k relevant chunks."""
        results = self.vectorstore.similarity_search(query, k=k)
        if not results:
            return None, None
        
        context = "\n---\n".join([doc.page_content for doc in results])
        metadata = {
            "source_url": results[0].metadata.get("source_url", "https://groww.in"),
            "extraction_date": results[0].metadata.get("extraction_date", "recent")
        }
        return context, metadata
