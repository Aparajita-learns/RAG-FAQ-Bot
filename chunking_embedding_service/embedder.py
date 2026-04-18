import os
import glob
from bs4 import BeautifulSoup
from langchain_community.document_loaders import BSHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_HTML_DIR = os.path.join(BASE_DIR, "data", "raw_html")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

def parse_html_to_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    # Get text, separated by spaces rather than immediately concatenated
    text = soup.get_text(separator=" ", strip=True)
    return text

def embed_and_store():
    # 1. Load HTML files
    html_files = glob.glob(os.path.join(RAW_HTML_DIR, "*.html"))
    if not html_files:
        print("No HTML files found in data/raw_html/")
        return

    documents = []
    
    # Simple document wrapper for Langchain
    class Document:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata

    for file in html_files:
        filename = os.path.basename(file)
        # Parse the filename expected format: name_date.html
        url_name = filename.replace(".html", "")
        # Extract text
        content = parse_html_to_text(file)
        
        metadata = {
            "source": filename,
            "url_slug": url_name
        }
        documents.append(Document(page_content=content, metadata=metadata))

    print(f"Loaded {len(documents)} raw files.")

    # 2. Chunking
    # 500-1000 tokens translates safely to ~1000-2000 chars roughly.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    # 3. Embedding Generation
    # Using bge-small-en-v1.5 per the architecture rule for < 20 URLs
    model_name = "BAAI/bge-small-en-v1.5"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True} # BGE models require normalized embeddings

    print(f"Loading embedding model: {model_name}... (this may download on first run)")
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    # 4. Vector Database Upsertion (Chroma Cloud)
    print("Upserting to Chroma Cloud...")
    
    chroma_host = os.environ.get("CHROMA_HOST", "api.trychroma.com")
    chroma_api_key = os.environ.get("CHROMA_API_KEY", "")
    chroma_database = os.environ.get("CHROMA_DATABASE", "RAG_chatbot_database")
    chroma_tenant = os.environ.get("CHROMA_TENANT", "55f74872-3fe6-4e35-ab34-fd70ca9022fc")
    
    if not chroma_api_key:
        print("WARNING: CHROMA_API_KEY environment variable not found. Cloud upsertion will fail.")
        
    # Initialize the Chroma HTTP client
    chroma_client = chromadb.HttpClient(
        host=chroma_host,
        headers={"x-chroma-token": chroma_api_key},
        database=chroma_database,
        tenant=chroma_tenant
    )
    
    # Upsert documents via LangChain Chroma wrapper
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings,
        client=chroma_client,
        collection_name="mutual_fund_faqs"
    )
    print("Successfully embedded and synced to Chroma Cloud.")

if __name__ == "__main__":
    embed_and_store()
