import os
import glob
from huggingface_hub import InferenceClient
from typing import List
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        # Using bge-small-en-v1.5 as per architecture rules
        # Using hosted Inference API to save memory
        self.model_name = "BAAI/bge-small-en-v1.5"
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not hf_token:
            # We fail early if token is missing
            raise ValueError("HUGGINGFACEHUB_API_TOKEN not found for Chunker.")

        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not hf_token:
            raise ValueError("HUGGINGFACEHUB_API_TOKEN not found for Chunker.")

        # Official Lightweight Inference Client
        class RemoteEmbeddings:
            def __init__(self, token, model_name):
                self.client = InferenceClient(api_key=token)
                self.model_name = model_name
            
            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                # Inference API handles batch inputs nicely
                return self.client.feature_extraction(texts, model=self.model_name).tolist()

            def embed_query(self, text: str) -> List[float]:
                # Returns a single list of floats
                return self.client.feature_extraction(text, model=self.model_name).tolist()

        self.embeddings = RemoteEmbeddings(hf_token, self.model_name)

    def parse_html(self, filepath):
        """Parses a local HTML file and returns clean text."""
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        return soup.get_text(separator=" ", strip=True)

    def create_chunks(self, folder_path):
        """Loads HTML files from a folder and returns LangChain document chunks."""
        html_files = glob.glob(os.path.join(folder_path, "*.html"))
        documents = []
        
        class Document:
            def __init__(self, page_content, metadata):
                self.page_content = page_content
                self.metadata = metadata

        for file in html_files:
            content = self.parse_html(file)
            metadata = {
                "source": os.path.basename(file),
                "extraction_date": "recent"
            }
            documents.append(Document(page_content=content, metadata=metadata))

        return self.text_splitter.split_documents(documents)

    def get_embedding_function(self):
        return self.embeddings
