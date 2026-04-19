# RAG Architecture: Mutual Fund FAQ Assistant

## 1. System Overview
This document outlines the Retrieval-Augmented Generation (RAG) architecture for a facts-only Mutual Fund FAQ Assistant. The system is designed to provide concise, verifiable, and source-backed answers to objective mutual fund queries while strictly avoiding investment advice.

The architecture is divided into three main pipelines:
1. **Data Ingestion & Indexing Pipeline** (Offline phase)
2. **Retrieval & Generation Pipeline** (Online phase)
3. **Application & UI Layer**

---

## 2. High-Level Architecture Diagram
*(Conceptual Text Representation)*
```
[User Interface] <---> [Application Backend (Thread Manager)]
                               |
                               v
                     [Input Guardrails & Moderation]
                       (PII Filter, Query Intent)
                               |
                               v
[Knowledge Base] ---> [Query Processing & Retrieval] <---> [Vector Database]
(AMC, SEBI, AMFI)              |
                               v
                       [Prompt Manager]
                               |
                               v
                     [Large Language Model (LLM)]
                               |
                               v
                    [Output Guardrails & Formatter]
                 (Length Limit, Citation, Footer Injection)
                               |
                               v
                        [User Response]
```

---

## 3. Component Details

### A. Data Ingestion & Indexing Pipeline
This pipeline is automated via **GitHub Actions** acting as a Scheduler. A CRON job runs every day at 9:15 AM to trigger the ingestion workflows, fetching the latest data and ensuring the local knowledge base is up to date.
1. **Scraping Service / Source Connectors:** A dedicated service to scrape and extract data from a predefined list of specific URLs. In scope, we will extract data from these URLs:
   - https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
   - https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
   - https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth
   - https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
   - https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
2. **Document Loaders:** Parsers for different document types: HTML (Web FAQs). *Currently no PDFs we will provide.*
### B. Chunking & Embedding Architecture
A dedicated sub-system handles how raw scraped content is processed and represented:
1. **HTML Parsing & Cleaning:** The HTML text is cleaned (e.g., using BeautifulSoup), stripping navigation menus, footers, and scripts to isolate the main mutual fund Q&A and factual data.
2. **Chunking Strategy:** 
   - Employs a semantic chunker (like `RecursiveCharacterTextSplitter`) prioritizing boundaries like `<h2>` or `<h3>` tags that naturally divide FAQ pairs.
   - Chunk size of ~500-1000 tokens with a 10% overlap to preserve contiguous context across split paragraphs.
   - **Crucial Metadata Attribution:** Every chunk dictionary is strictly injected with its `source_url`, `content_type` (HTML), and `extraction_date`.
3. **Embedding Generation:** 
   - Text chunks are processed in batches.
   - **Model:** We strictly use open-source HuggingFace models instead of OpenAI. 
     - *Scale Rule:* Use `BAAI/bge-small-en-v1.5` for the current scope of 5 URLs. If expanding to 20+ URLs, scale up to `BAAI/bge-base-en-v1.5`.
4. **Database Upsertion (Chroma Cloud):** 
   - Following extraction, embeddings and metadata payloads are pushed securely to **Chroma Cloud (trychroma.com)**. 
   - The GitHub Action runner authenticates using a `CHROMA_API_KEY` to sync the latest daily data, ensuring the web application queries a managed cloud database rather than a local file.

---

## 4. Automation Scheduler (GitHub Actions)

The entire ingestion pipeline is automated via GitHub Actions to ensure the bot always has the most current Mutual Fund data.

- **Trigger:** Daily at **9:15 AM IST** (03:45 UTC).
- **Execution Order:**
  1. **Scraping Service:** Fetches latest HTML from target Groww URLs.
  2. **Data Persistence:** Automatically commits raw HTML updates back to the GitHub repository.
  3. **Chunking & Embedding Service:**
     - Reads the fresh HTML files.
     - Performs semantic chunking (1000 char size).
     - Generates BGE embeddings locally on the GH runner.
     - Upserts/updates the **Chroma Cloud** database collection.
  4. **Verification:** Runs a diagnostic check to confirm the total document count in the cloud.



### C. Retrieval & Generation Pipeline
This pipeline processes user queries in real-time.
1. **Input Guardrails & Preprocessing:**
   - **PII Scrubbing:** Pattern matching (Regex/NER) to block and immediately reject queries containing PAN, Aadhaar, account numbers, email, or phone numbers.
   - **Intent Classification:** A lightweight classifier to identify advisory/predictive queries ("Should I invest?", "Which is better?"). If flagged, the system bypasses retrieval and triggers the **Refusal Handler**.
2. **Query Embedding:** Converts the sanitized query into a vector representation using the same embedding model.
3. **Semantic Retrieval:** 
   - Performs a Top-K (e.g., K=3 or 5) nearest neighbor search in the Vector Database.
   - May utilize Hybrid Search (fusion of vector similarity + keyword matching via BM25) to accurately match specific fund names and objective metrics like "Expense ratio".
4. **Prompt Engineering Engine:** Assembles a restricted context prompt. 
   - *System Prompt Rules:* "You are a factual mutual fund assistant. Use ONLY the provided context. Answer in maximum 3 sentences. Do not offer advice. Include the exact source link."
5. **LLM Generation:** A generative model (e.g., GPT-3.5/4-Turbo, Claude 3 Haiku, or fine-tuned Llama-3) produces the final response based solely on the retrieved chunks.

### D. Output Formatter & Post-Processing
Enforces the final delivery bounds defined in the requirements.
1. **Brevity Truncation:** Ensures the response does not exceed the 3-sentence limit.
2. **Citation Injection:** Appends the exact source URL associated with the referenced chunk.
3. **Footer Appender:** Always affixes: `Last updated from sources: <date>`.

### E. Application & UI Layer
1. **Session & Thread Management:** Uses a lightweight persistent store (e.g., Redis or SQLite) to manage `session_id` and maintain multi-threaded, independent chat histories per user.
2. **Minimalist Frontend:** 
   - Built with specialized chat UI components (e.g., Streamlit, Gradio, or a React-based chat window).
   - Features a permanent, unmissable banner: *"Facts-only. No investment advice."*
   - Includes 3 clickable initial template questions.

---

## 4. Refusal Handling Flow
A critical structural aspect to satisfy compliance:
- **Trigger:** If the user query is classified as an opinion, comparison across AMCs, or seeking investment advice.
- **Action:** LLM generation strictly halts.
- **Output Template:** "I am an objective assistant and cannot provide investment advice or recommendations. Please refer to certified financial advisors or official [AMFI](https://www.amfiindia.com) / [SEBI](https://www.sebi.gov.in) resources for guidance."

## 5. Security & Constraint Measures
- **Data Privacy:** Local PII scrubbers ensure sensitive identifiers are never sent to external LLM APIs.
- **Hallucination Prevention:** By keeping temperature low (0.0 to 0.1) and strictly grounding answers to the supplied "Context block" (RAG strict mode).
- **No Calculators Built-in:** Assures no performance calculations or return forecasts can be executed natively.

## 6. Technology Stack Suggestion (Lightweight)
- **Framework:** LangChain or LlamaIndex
- **Vector DB:** ChromaDB (Local/Embedded) or Qdrant
- **LLM/Embeddings:** OpenAI API or Anthropic API (for capability) / Local LLMs via Ollama (for strict privacy)
- **Backend/UI:** FastAPI (backend) + Streamlit/Gradio (frontend)
