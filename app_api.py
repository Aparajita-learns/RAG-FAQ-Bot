import os
from dotenv import load_dotenv
from modules.retrieval.coordinator import QueryProcessor
from modules.ui.server import UIServer

# Load environment variables (API Keys, etc.)
load_dotenv()

# Initialize the modular RAG engine
processor = QueryProcessor()

# Initialize the UI Server with the processor
ui_server = UIServer(processor=processor)

# Expose the FastAPI app for uvicorn
app = ui_server.app

if __name__ == "__main__":
    import uvicorn
    # To run: python app_api.py
    # Or: uvicorn app_api:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
