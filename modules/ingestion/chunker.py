import os
import glob
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

class Chunker:
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        # Using bge-small-en-v1.5 as per architecture rules
        self.model_name = "BAAI/bge-small-en-v1.5"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

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
