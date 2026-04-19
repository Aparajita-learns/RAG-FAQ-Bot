import os
import requests
import datetime
import urllib.parse
from bs4 import BeautifulSoup

class Scraper:
    def __init__(self, data_dir="data/raw_html"):
        self.data_dir = data_dir
        self.urls = [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
            "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        ]
        os.makedirs(self.data_dir, exist_ok=True)

    def clean_html(self, html_content):
        """Minimal cleaning of HTML to remove noise."""
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "noscript", "meta", "link", "header", "footer", "nav"]):
            tag.decompose()
        return str(soup)

    def scrape_all(self):
        """Scrapes all URLs and saves cleaned HTML to the data directory."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        saved_files = []

        for url in self.urls:
            print(f"Scraping {url}...")
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Extract fund name for filename
                fund_name = urllib.parse.urlparse(url).path.strip("/").split("/")[-1]
                clean_content = self.clean_html(response.text)
                
                filename = f"{fund_name}_{timestamp}.html"
                filepath = os.path.join(self.data_dir, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(clean_content)
                
                saved_files.append(filepath)
                print(f"  [OK] Saved to {filename}")
                
            except Exception as e:
                print(f"  [FAILED] Error scraping {url}: {e}")
        
        return saved_files
