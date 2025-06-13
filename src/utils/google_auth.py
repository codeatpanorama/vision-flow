import os
from pathlib import Path
from google.cloud import vision
from google.oauth2 import service_account

def setup_google_vision_auth():
    """
    Sets up Google Cloud Vision authentication using service account credentials.
    The credentials file path should be specified in GOOGLE_APPLICATION_CREDENTIALS env var.
    
    Returns:
        vision.ImageAnnotatorClient: Authenticated Google Vision client
    
    Raises:
        FileNotFoundError: If credentials file is not found
        ValueError: If credentials environment variable is not set
    """
    # Check if credentials path is set
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. "
            "Please set it to the path of your service account JSON file."
        )
    
    credentials_path = Path(credentials_path)
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Google Cloud credentials file not found at: {credentials_path}\n"
            "Please download your service account JSON file from Google Cloud Console "
            "and set the correct path in .env file."
        )
    
    try:
        # Create credentials object
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=['https://www.googleapis.com/auth/cloud-vision']
        )
        
        # Create and return authenticated client
        return vision.ImageAnnotatorClient(credentials=credentials)
    
    except Exception as e:
        raise Exception(f"Failed to initialize Google Vision client: {str(e)}") 