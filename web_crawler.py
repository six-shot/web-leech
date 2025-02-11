import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Set

# Define target URL and file types
BASE_URL = "https://www.uscis.gov/administrative-appeals/aao-decisions/aao-non-precedent-decisions?items_per_page=10"
DOWNLOAD_FOLDER = "downloads"
FILE_EXTENSIONS = [".pdf", ".zip"]  # Add more extensions if needed

class WebCrawler:
    def __init__(self, base_url: str, download_folder: str, file_extensions: List[str], delay: float = 1.0):
        self.base_url = base_url
        self.download_folder = download_folder
        self.file_extensions = file_extensions
        self.delay = delay  # Delay between requests in seconds
        self.downloaded_files: Set[str] = set()
        
        # Create downloads folder if not exists
        os.makedirs(download_folder, exist_ok=True)

    def download_file(self, url: str) -> bool:
        """Download a file from the given URL."""
        try:
            # Skip if already downloaded
            if url in self.downloaded_files:
                print(f"Skipping (already downloaded): {url}")
                return False

            local_filename = os.path.join(self.download_folder, url.split("/")[-1])
            
            # Check if file already exists
            if os.path.exists(local_filename):
                print(f"File already exists: {local_filename}")
                return False

            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(local_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            self.downloaded_files.add(url)
            print(f"Successfully downloaded: {local_filename}")
            return True
            
        except requests.RequestException as e:
            print(f"Error downloading {url}: {str(e)}")
            return False

    def crawl(self) -> None:
        """Start crawling from the base URL and handle pagination."""
        page = 0
        while True:
            page_url = f"{self.base_url}&page={page}"
            try:
                print(f"Crawling page {page}...")
                response = requests.get(page_url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                links = soup.find_all("a", href=True)
                
                # Check if we found any links on this page
                found_files = False
                for link in links:
                    file_url = urljoin(self.base_url, link["href"])
                    if any(file_url.endswith(ext) for ext in self.file_extensions):
                        found_files = True
                        if self.download_file(file_url):
                            # Add delay between downloads to be polite
                            time.sleep(self.delay)
                
                # If no files found on this page, we've reached the end
                if not found_files:
                    print(f"No more files found after page {page}. Stopping.")
                    break
                
                page += 1
                        
            except requests.RequestException as e:
                print(f"Error accessing {page_url}: {str(e)}")
                break

def main():
    # Configuration
    BASE_URL = "https://www.uscis.gov/administrative-appeals/aao-decisions/aao-non-precedent-decisions?items_per_page=10"
    DOWNLOAD_FOLDER = "downloads"
    FILE_EXTENSIONS = [".pdf", ".zip"]
    
    # Create and run crawler
    crawler = WebCrawler(
        base_url=BASE_URL,
        download_folder=DOWNLOAD_FOLDER,
        file_extensions=FILE_EXTENSIONS
    )
    crawler.crawl()

if __name__ == "__main__":
    main()
