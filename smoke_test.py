import os
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

def run_smoke_test():
    print("Loading embedding model...")
    model_name = "BAAI/bge-small-en-v1.5"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}
    
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    print("Loading Vector DB (FAISS)...")
    # allow_dangerous_deserialization=True is required for loading FAISS files starting in recent LangChain versions
    vectorstore = FAISS.load_local(CHROMA_DB_DIR, embeddings, allow_dangerous_deserialization=True)

    query = "What is the exit load or expense ratio for HDFC Mutual fund?"
    print(f"\nRunning Smoke Test Query: '{query}'")
    
    results = vectorstore.similarity_search(query, k=2)

    print("\n--- SMOKE TEST RESULTS ---")
    if not results:
        print("No results found. Vector DB might be empty.")
    
    for i, doc in enumerate(results):
        print(f"\n[Result {i+1}]")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Content snippet: {doc.page_content.strip()}")

if __name__ == "__main__":
    run_smoke_test()
