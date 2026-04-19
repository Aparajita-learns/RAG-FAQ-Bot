import os
import chromadb
from langchain_chroma import Chroma

class DBUpdater:
    def __init__(self):
        # Configure Chroma Cloud credentials from environmental variables
        self.host = os.environ.get("CHROMA_HOST", "https://api.trychroma.com")
        if not self.host.startswith("http"):
            self.host = f"https://{self.host}"
            
        self.api_key = os.environ.get("CHROMA_API_KEY", "")
        self.database = os.environ.get("CHROMA_DATABASE", "RAG_chatbot_database")
        self.tenant = os.environ.get("CHROMA_TENANT", "55f74872-3fe6-4e35-ab34-fd70ca9022fc")

    def get_client(self):
        """Initializes the Chroma HTTP Client."""
        return chromadb.HttpClient(
            host=self.host,
            headers={"x-chroma-token": self.api_key},
            database=self.database,
            tenant=self.tenant,
            ssl=True
        )

    def upsert_documents(self, chunks, embedding_function, collection_name="mutual_fund_faqs"):
        """Syncs provide chunks to Chroma Cloud in batches."""
        client = self.get_client()
        vectorstore = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embedding_function
        )

        batch_size = 50
        print(f"Syncing {len(chunks)} chunks in batches of {batch_size}...")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            vectorstore.add_documents(batch)
            print(f"  [OK] Synced batch {i//batch_size + 1}")
        
        print("Cloud Sync Complete.")
