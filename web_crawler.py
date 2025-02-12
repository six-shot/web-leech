import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Set
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

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
        
        # Initialize Google Drive service
        self.drive_service = self._initialize_drive_service()
        
        # Create folder in Google Drive if it doesn't exist
        self.folder_id = self._create_or_get_folder(download_folder)

    def _initialize_drive_service(self):
        """Initialize and return Google Drive service."""
        from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE
        creds = None
        
        # Load or create credentials
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)

    def _create_or_get_folder(self, folder_name: str) -> str:
        """Create or get Google Drive folder ID."""
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = self.drive_service.files().list(q=query).execute()
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        else:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = self.drive_service.files().create(
                body=file_metadata, fields='id'
            ).execute()
            return file.get('id')

    def download_file(self, url: str) -> bool:
        """Download a file from the given URL and upload to Google Drive."""
        try:
            # Skip if already downloaded
            if url in self.downloaded_files:
                print(f"Skipping (already downloaded): {url}")
                return False

            filename = url.split("/")[-1]
            
            # Download file to memory
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            # Upload to Google Drive
            fh = io.BytesIO(response.content)
            media = MediaIoBaseUpload(fh, mimetype='application/pdf', resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            self.downloaded_files.add(url)
            print(f"Successfully uploaded to Google Drive: {filename}")
            return True
            
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
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
    from config import BASE_URL, DOWNLOAD_FOLDER, FILE_EXTENSIONS
    
    # Create and run crawler
    crawler = WebCrawler(
        base_url=BASE_URL,
        download_folder=DOWNLOAD_FOLDER,
        file_extensions=FILE_EXTENSIONS
    )
    crawler.crawl()

if __name__ == "__main__":
    main()