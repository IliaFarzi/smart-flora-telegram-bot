import json
import os
import requests
from dotenv import load_dotenv
import logging

from iran_time import IranTime

iran_time = IranTime()

load_dotenv()
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Proxy settings for Iranian networks
PROXY = {
    "http": os.getenv('HTTP_IR_PROXY'),
}


class MetisUploader:
    def __init__(self):
        self.metis_api_key = os.getenv('METIS_API_KEY')
        self.storage_endpoint = "https://api.metisai.ir/api/v1/storage"
        if not self.metis_api_key:
            logger.error("Metis API key is missing. Please check your .env file.")
            raise ValueError("Metis API key is missing.")

    def upload_file(self, file_path: str) -> str:
        """Uploads a file to Metis storage and returns the file URL if successful."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""

        try:
            with open(file_path, "rb") as file:
                headers = {
                    "Authorization": f"Bearer {self.metis_api_key}"
                }
                files = {
                    "files": file,
                }

                response = requests.post(self.storage_endpoint, headers=headers, files=files, proxies=PROXY,
                                         verify=False)

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
        self.wrapper_endpoint = "https://api.metisai.ir/api/v1/chat/session"
        if not self.metis_api_key:
            logger.error("Metis API key is missing. Please check your .env file.")
            raise ValueError("Metis API key is missing.")
        if not self.metis_bot_id:
            logger.error("Metis Bot ID is missing. Please check your .env file.")
            raise ValueError("Metis Bot ID is missing.")

    def analyze_image(self, image_url: str, selected_city: str, hour: str, month: str, environment: str):
        prompt = (
            f"According to the provided image's captured in {hour} in {selected_city},Iran\n"
            f"recommend two {environment} plants based on these criteria:\n"
            f"0. Keep in mind this picture is taken in {month} so suggested plant should be according to season\n"
            f"1. Plants should be suitable for {environment} and compatible with {selected_city}'s climate and regional biomes.\n"
            f"2. {'Lighting(should be inferred form clues from image like windows) with respect to time of day image is taken and space available should be emphasized for suggested plants' if environment == 'indoor' else 'Climate, regional biome and season should be emphasized for suggested plants'}.\n"
            "3. Avoid recommending any illegal plants.\n\n"
            "Output in JSON format with the following structure:\n"
            "   - *Note:* If the image is other than a place where a plant can be placed, "
            "you should return {\"error\": \"badImage\", \"plants\":[] }.\n\n"
            "{\n"
            "  \"plants\": [\n"
            "    {\n"
            "      \"scientificName\": \"Example plant name\",\n"
            "      \"persianCommonName\": \"اسم فارسی\",\n"
            "      \"description\": \"Detailed care instructions in Persian. and some clause on why this plant is suitable for situation, if a date is mentioned here should be in Jalali format and Farsi\""
            "    }\n"
            "  ],\n"
            "  \"error\": null\n"
            "}"
            "   - *critical note:* response is invalid if it is wrapped in ```{any language}```, and some thing like ```json``` should not be used in response"

        )
        """Send the image URL to Metis API for plant analysis and get recommendations."""

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
            session_response = requests.post(self.wrapper_endpoint, headers=headers, json=session_data, proxies=PROXY,
                                             verify=False)
            session_response.raise_for_status()
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

            response = requests.post(
                f'https://api.metisai.ir/api/v1/chat/session/{session_id}/message',
                headers=headers, json=data, proxies=PROXY, verify=False
            )
            response.raise_for_status()

            response_data = response.json()

            try:
                # Try to parse the content as JSON
                plant_object = json.loads(response_data['content'])
            except (json.JSONDecodeError, TypeError):
                logger.error(f"Invalid JSON response: {response_data['content']}")
                return {"error": "Invalid response format", "plants": []}

            # Validate response format
            if isinstance(plant_object, dict):
                if "error" in plant_object and plant_object["error"] == "badImage":
                    return {"error": "Please provide clearer images of your space.", "plants": []}
                elif "plants" in plant_object:
                    return {"plants": plant_object["plants"], "error": None}

            return {"error": "Invalid response format", "plants": []}

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
        res = suggestion.analyze_image(image_url, 'Tehran', iran_time.get_current_hour_am_pm(),
                                       iran_time.get_current_month_name(), environment='indoor')
        print(res)
    else:
        print("Image upload failed.")
