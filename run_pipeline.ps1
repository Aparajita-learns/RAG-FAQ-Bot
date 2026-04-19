# Mutual Fund RAG Pipeline Runner
# This script runs the local scraper, embedder, and verification in one sequence.

# 1. Environment Check
if (-not $env:CHROMA_API_KEY) {
    Write-Host "ERROR: CHROMA_API_KEY environment variable is not set." -ForegroundColor Red
    Write-Host "Please set it using: `$env:CHROMA_API_KEY='your_key_here'" -ForegroundColor Yellow
    exit 1
}

if (-not $env:CHROMA_HOST) {
    $env:CHROMA_HOST = "api.trychroma.com"
}

if (-not $env:CHROMA_DATABASE) {
    $env:CHROMA_DATABASE = "RAG_chatbot_database"
}

if (-not $env:CHROMA_TENANT) {
    $env:CHROMA_TENANT = "55f74872-3fe6-4e35-ab34-fd70ca9022fc"
}

Write-Host "--- STEP 1: Starting Scraping Service ---" -ForegroundColor Cyan
python scraping_service/scraper.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Scraper failed. Aborting." -ForegroundColor Red
    exit 1
}

Write-Output "" # Newline
Write-Host "--- STEP 2: Starting Chunking and Embedding Service ---" -ForegroundColor Cyan
Write-Host "(This will upload vectors to Chroma Cloud)" -ForegroundColor DarkGray
python chunking_embedding_service/embedder.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Embedder failed. Check if you have installed C++ Build Tools and ran 'pip install chromadb'." -ForegroundColor Red
    exit 1
}

Write-Output "" # Newline
Write-Host "--- STEP 3: Verifying Cloud State ---" -ForegroundColor Cyan
python chunking_embedding_service/check_chroma.py

Write-Output "" # Newline
Write-Host "Pipeline execution complete!" -ForegroundColor Green
