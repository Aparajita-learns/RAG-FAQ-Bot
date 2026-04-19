import os
from dotenv import load_dotenv
from modules.retrieval.coordinator import QueryProcessor
from modules.ui.server import UIServer

# Load environment variables (API Keys, etc.)
load_dotenv()

# Initialize the modular RAG engine
processor = QueryProcessor()

# Initialize the UI Server as a pure API
ui_server = UIServer(processor=processor)

# Expose the FastAPI app for uvicorn
app = ui_server.app

if __name__ == "__main__":
    import uvicorn
    # To run local for development: python main.py
    # For production deployment: uvicorn main:app --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
