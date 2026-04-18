import os
import chromadb

def check_chroma_state():
    chroma_host = os.environ.get("CHROMA_HOST", "api.trychroma.com")
    chroma_api_key = os.environ.get("CHROMA_API_KEY")
    chroma_database = os.environ.get("CHROMA_DATABASE", "RAG_chatbot_database")

    if not chroma_api_key:
        print("ERROR: CHROMA_API_KEY environment variable not found.")
        return

    print(f"Connecting to Chroma Cloud (DB: {chroma_database}) at: {chroma_host}")
    
    try:
        # Initialize the Chroma HTTP client
        client = chromadb.HttpClient(
            host=chroma_host,
            headers={"x-chroma-token": chroma_api_key},
            database=chroma_database
        )

        # List all collections
        collections = client.list_collections()
        print(f"\nFound {len(collections)} collection(s):")
        
        target_collection = "mutual_fund_faqs"
        found = False
        
        for col in collections:
            count = col.count()
            print(f"- Collection: '{col.name}' | Documents: {count}")
            if col.name == target_collection:
                found = True
        
        if not found:
            print(f"\nWARNING: '{target_collection}' was NOT found in the list above.")
        else:
            print(f"\nSUCCESS: '{target_collection}' exists and is reachable.")
            
    except Exception as e:
        print(f"Failed to connect to Chroma Cloud: {e}")

if __name__ == "__main__":
    check_chroma_state()
