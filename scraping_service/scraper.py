import os
import datetime
import requests
from bs4 import BeautifulSoup
import urllib.parse

# List of URLs to scrape
URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
]

# Configure directories
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_html")

def setup_directories():
    os.makedirs(DATA_DIR, exist_ok=True)

def extract_fund_name_from_url(url):
    """Extracts a readable filename from the URL."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    return path.strip("/").split("/")[-1]

def clean_html(html_content):
    """Minimal cleaning of HTML before saving, to reduce size."""
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script and style elements
    for script_or_style in soup(["script", "style", "noscript", "meta", "link", "header", "footer", "nav"]):
        script_or_style.decompose()
    
    return str(soup)

def scrape_urls():
    setup_directories()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    
    for url in URLS:
        print(f"Scraping {url}...")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            fund_name = extract_fund_name_from_url(url)
            clean_content = clean_html(response.text)
            
            # Save the file
            filename = f"{fund_name}_{timestamp}.html"
            filepath = os.path.join(DATA_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(clean_content)
                
            print(f"Successfully saved to {filepath}")
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")

if __name__ == "__main__":
    scrape_urls()
