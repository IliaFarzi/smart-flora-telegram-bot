import json
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

# Proxy settings for Iranian networks
PROXY = {
    "http": "http://80.249.112.162:80",
    "https": "http://80.249.112.162:80"
}

class MetisUploader:
    def __init__(self):
        self.metis_api_key = os.getenv('METIS_API_KEY')
        self.storage_endpoint = "https://api.metisai.ir/api/v1/storage"  # Metis storage API endpoint
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
                    "files": file,
                }

                response = requests.post(self.storage_endpoint, headers=headers, files=files)

                # Check if the upload was successful
                if response.status_code == 200:
                    response_data = response.json()
                    file_url = response_data['files'][0]['url']
                    if file_url:
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

class MetisSuggestion:
    def __init__(self):
        self.metis_api_key = os.getenv('METIS_API_KEY')
        self.metis_bot_id = os.getenv('METIS_BOT_ID')
        self.wrapper_endpoint = "https://api.metisai.ir/api/v1/chat/session"  # Wrapper endpoint for image processing
        if not self.metis_api_key:
            logger.error("Metis API key is missing. Please check your .env file.")
            raise ValueError("Metis API key is missing.")
        if not self.metis_bot_id:
            logger.error("Metis Bot ID is missing. Please check your .env file.")
            raise ValueError("Metis Bot ID is missing.")

    def analyze_image(self, image_url: str):
        """Send the image URL to Metis API for plant analysis and get recommendations."""
        prompt = (
            "According to the provided image's lighting conditions and available space, "
            "recommend two indoor plants based on these criteria:\n"
            "1. Plants should be easy to find and not rare.\n"
            "2. Plants should be suitable for indoor environments and compatible with Tehran's climate.\n"
            "3. Avoid recommending any illegal plants.\n\n"
            "Output in JSON format with the following structure:\n"
            "   - *Note:* If the image is other than a place where a plant can be placed, "
            "you should return {\"error\": \"badImage\", \"plants\":[] }.\n\n"
            "{\n"
            "  \"plants\": [\n"
            "    {\n"
            "      \"scientificName\": \"Example plant name\",\n"
            "      \"persianCommonName\": \"اسم فارسی\",\n"
            "      \"description\": \"Detailed care instructions in Persian.\""
            "    }\n"
            "  ],\n"
            "  \"error\": null\n"
            "}"
            "   - *Note:* we use your should be parseable as json file without ```json```"

        )
        # Set up the initial session data
        session_data = {
            "botId": self.metis_bot_id,
            "user": None,
        }
        headers = {
            "Authorization": f"Bearer {self.metis_api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Initiate session
            session_response = requests.post(self.wrapper_endpoint, headers=headers, json=session_data)
            session_response.raise_for_status()  # Raise exception if the request was unsuccessful
            session_id = session_response.json()['id']
            if not session_id:
                logger.error("Session ID not returned in response.")
                return {"error": "Unable to initiate Metis session.", "plants": []}
            data = {
                "message": {
                    "type": "USER",
                    "content": prompt,
                    "attachments": [
                        {
                            "content": image_url,
                            "contentType": "IMAGE"
                        }
                    ]
                }
            }
            # Send the image for analysis
            response = requests.post(
                f'https://api.metisai.ir/api/v1/chat/session/{session_id}/message',
                headers=headers, json=data
            )
            response.raise_for_status()  # Raise an exception if the request failed

            response_data = response.json()

            # Check the 'choices' and extract the plant data
            plant_object = json.loads(response_data['content']) or {'error': 'noPlant', 'plants': []}

            # Validate and return response
            if isinstance(plant_object, str) or 'error' in plant_object and plant_object['error'] == "badImage":
                return {"error": "Please provide clearer images of your space.", "plants": []}
            elif not plant_object.get('plants'):
                return {"error": "No suitable plants found for the provided image.", "plants": []}

            return {"plants": json.loads(plant_object.get("plants", [])), "error": None}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"error": "Unable to retrieve plant recommendations at this time.", "plants": []}
        except Exception as e:
            logger.error(f"Error processing image with Metis API: {e}")
            return {"error": "An unexpected error occurred during processing.", "plants": []}


# Usage
if __name__ == "__main__":
    uploader = MetisUploader()
    image_url = uploader.upload_file('uploads/photo_5846132522528916670_y.jpg')
    if image_url:
        suggestion = MetisSuggestion()
        res = suggestion.analyze_image(image_url)
        print(res)
    else:
        print("Image upload failed.")
