import os
import chromadb

class DBUpdater:
    def __init__(self):
        # Configure Chroma Cloud host (api.chromadb.com)
        self.host = os.environ.get("CHROMA_HOST", "api.chromadb.com")
        if not self.host.startswith("http"):
            self.host = f"https://{self.host}"
            
        self.api_key = os.environ.get("CHROMA_API_KEY", "")
        self.database = os.environ.get("CHROMA_DATABASE", "RAG_chatbot_database")
        self.tenant = os.environ.get("CHROMA_TENANT", "55f74872-3fe6-4e35-ab34-fd70ca9022fc")

    def get_client(self):
        """Initializes the lightweight Chroma HTTP Client."""
        return chromadb.HttpClient(
            host=self.host,
            headers={"x-chroma-token": self.api_key},
            database=self.database,
            tenant=self.tenant,
            ssl=True
        )

    def upsert_documents(self, chunks, embedding_function, collection_name="mutual_fund_faqs"):
        """Syncs provide chunks to Chroma Cloud directly using the SDK."""
        client = self.get_client()
        collection = client.get_or_create_collection(name=collection_name)

        print(f"Syncing {len(chunks)} chunks...")
        
        # Prepare data for Chroma SDK
        documents = [c.page_content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        ids = [f"id_{i}_{os.urandom(4).hex()}" for i in range(len(chunks))]
        
        # Generate embeddings using our RemoteEmbeddings class
        embeddings = embedding_function.embed_documents(documents)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        print("Cloud Sync Complete.")
