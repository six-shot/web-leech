# Google Drive API configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Crawler configuration
BASE_URL = "https://www.uscis.gov/administrative-appeals/aao-decisions/aao-non-precedent-decisions?items_per_page=10"
DOWNLOAD_FOLDER = "downloads"
FILE_EXTENSIONS = [".pdf", ".zip"]
