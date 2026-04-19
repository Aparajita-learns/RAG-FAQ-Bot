import os
from dotenv import load_dotenv
from modules.ingestion.scraper import Scraper
from modules.ingestion.chunker import Chunker
from modules.ingestion.db_updater import DBUpdater

def run_ingestion():
    load_dotenv()
    
    # 1. Initialize Modules
    scraper = Scraper()
    chunker = Chunker()
    db_updater = DBUpdater()
    
    # 2. Scrape Latest Data
    print("--- Phase 1: Scraping ---")
    scraper.scrape_all()
    
    # 3. Process Files
    print("\n--- Phase 2: Chunking & Embedding ---")
    raw_data_path = os.path.join(os.getcwd(), "data", "raw_html")
    print(f"Loading files from {raw_data_path}...")
    
    chunks = chunker.create_chunks(raw_data_path)
    if not chunks:
        print("No chunks created. Check if data/raw_html is empty.")
        return
        
    # 3. Update DB
    db_updater.upsert_documents(
        chunks=chunks, 
        embedding_function=chunker.get_embedding_function()
    )

if __name__ == "__main__":
    run_ingestion()
