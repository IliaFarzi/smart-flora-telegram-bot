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

class MetisSuggestion:
    def __init__(self):
        self.metis_api_key = os.getenv('METIS_API_KEY')
        self.chat_api_endpoint = "https://api.metisai.ir/api/session"  # Metis Chat API endpoint
        if not self.metis_api_key:
            logger.error("Metis API key is missing. Please check your .env file.")
            raise ValueError("Metis API key is missing.")

    def analyze_image(self, image_url: str):
        """Send the image URL to Metis API for plant analysis and get recommendations."""
        prompt = (
            "According to the provided image's lighting conditions and available space, "
            "recommend two indoor plants based on these criteria:\n"
            "1. Plants should be easy to find and not rare.\n"
            "2. Plants should be suitable for indoor environments and compatible with Tehran's climate.\n"
            "3. Avoid recommending any illegal plants.\n\n"
            "Output in JSON format with the following structure:\n"
            "{\n"
            "  \"plants\": [\n"
            "    {\n"
            "      \"scientificName\": \"Example plant name\",\n"
            "      \"persianCommonName\": \"اسم فارسی\",\n"
            "      \"description\": \"Detailed care instructions in Persian.\",\n"
            "      \"url\": \"https://example.com/plant_image.jpg\"\n"
            "    }\n"
            "  ],\n"
            "  \"error\": null\n"
            "}"
        )

        # Prepare the data payload for the chat API
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
            },
            "max_tokens": 500,
        }

        headers = {
            "Authorization": f"Bearer {self.metis_api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Send the analysis request directly to the Metis chat API
            response = requests.post(self.chat_api_endpoint, headers=headers, json=data)

            if response.status_code == 200:
                response_data = response.json()
                logger.info(response_data)
                plant_object = response_data.get('choices', [{}])[0].get('message', {}).get('content', {})

                # Check for error or empty plant list in the response
                if 'error' in plant_object or plant_object.get('error') == "badImage":
                    return {"error": "Please provide clearer images of your space.", 'plants': []}
                elif not plant_object.get('plants'):
                    return {"error": "No suitable plants found for the provided image.", 'plants': []}

                # Return list of plants if valid data is received
                return {"plants": plant_object.get('plants', []), "error": "null"}
            else:
                logger.error(f"Error from Metis API: {response.status_code} - {response.text}")
                return {"error": "Unable to retrieve plant recommendations at this time.", 'plants': []}

        except Exception as e:
            logger.error(f"Error processing image with Metis API: {e}")
            return {'error': "Unable to retrieve plant recommendations due to an error.", 'plants': []}


# Usage
if __name__ == "__main__":
    uploader = MetisSuggestion()

    res = uploader.analyze_image(
        'https://tpsgsbxstorageaccount.blob.core.windows.net/tpsgsbxstoragecontainer/upload/329b6a04-2d92-4c9b-afae-3601514f4734/d7786984-fac8-429d-a78e-ca50fba1624b.jpg?sv=2023-11-03&se=2124-10-28T05%3A37%3A24Z&sr=c&sp=r&sig=VJazL63Dtyc%2BhdMaw3lk6Ivzn7FCmJ0GpRFI4Y56qxo%3D'
    )
    print(res)
