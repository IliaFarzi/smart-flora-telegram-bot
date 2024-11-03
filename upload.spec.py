import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MetisUploader:
    def __init__(self):
        self.metis_api_key = os.getenv('METIS_API_KEY')
        self.storage_endpoint = "https://api.metisai.ir/openai/v1/files"  # Metis storage API endpoint
        if not self.metis_api_key:
            logger.error("Metis API key is missing. Please check your .env file.")
            raise ValueError("Metis API key is missing.")

    def upload_file(self, file_path: str) -> str:
        """Uploads a file to Metis storage and returns the file URL if successful."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""

        try:
            # Open file in binary mode for upload
            with open(file_path, "rb") as file:
                headers = {
                    "Authorization": f"Bearer {self.metis_api_key}"
                }
                files = {
                    "file": file,
                    "purpose": 'vision'
                }

                logger.info(f"Uploading file: {file_path}")
                response = requests.post(self.storage_endpoint, headers=headers, files=files)

                # Check if the upload was successful
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(response_data)
                    logger.info('---------------------------------------')
                    file_url = response_data['files'][0]['url']
                    if file_url:
                        logger.info(f"File uploaded successfully. File URL: {file_url}")
                        return file_url
                    else:
                        logger.error("Upload response did not contain a file URL.")
                        return ""
                else:
                    logger.error(f"Failed to upload file. Status: {response.status_code}, Response: {response.text}")
                    return ""

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception during file upload: {e}")
            return ""

# Usage
if __name__ == "__main__":
    uploader = MetisUploader()
    # Make sure the file path exists in the upload folder
    file_path = os.path.join("uploads", "photo_5846132522528916670_y.jpg")  # Replace 'your_file.jpg' with your actual file name
    file_url = uploader.upload_file(file_path)

    if file_url:
        print(f"File uploaded successfully. URL: {file_url}")
    else:
        print("File upload failed.")