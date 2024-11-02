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
        self.wrapper_endpoint = "https://api.metisai.ir/openai/v1/chat/completions"  # Wrapper endpoint for image processing
        if not self.metis_api_key:
            logger.error("Metis API key is missing. Please check your .env file.")
            raise ValueError("Metis API key is missing.")

    def analyze_image(self, image_url: str):
        """Send the image URL to Metis API for plant analysis and get recommendations."""
        prompt = (
            "According to The provided images lighting conditions and available space. "
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

        data = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": [
                    {"type": "text", "text": "explan the image"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpg:base64,{image_url}"}}
                    ]
                 }
            ],
            "max_tokens": 500,
        }

        headers = {
            "Authorization": f"Bearer {self.metis_api_key}",
            "Content-Type": "application/json"
        }
        try:
            # Send the analysis request through the proxy
            response = requests.post(self.wrapper_endpoint, headers=headers, json=data)

            if response.status_code == 200:
                response_data = response.json()
                logger.info(response_data)
                plant_object = response_data['choices'][0]['message']['content']

                # Check for error in the response
                if type(response_data) == "string" or 'error' in plant_object or plant_object['error'] == "badImage":
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
        # 'https://tpsgsbxstorageaccount.blob.core.windows.net/tpsgsbxstoragecontainer/upload/7afaff13-edc2-4506-ad05-9ba537065641/ff93e065-e68d-4e8e-b347-a1b045cf5494.jpg?sv=2023-11-03&se=2124-11-02T14%3A02%3A02Z&sr=c&sp=r&sig=pLHbvrFZMcO%2BfnMiX%2Fl0%2FnZMDNLOW4S%2BlqBnbWjHnVE%3D'
  # 'https://www.marthastewart.com/thmb/JlKSNX1MKC3eHUd-sbHTh79VCJQ=/750x0/filters:no_upscale():max_bytes(150000):strip_icc():format(webp)/pacific-northwest-home-tour-great-room-0820-14d61b428237459b9e996c769ae92dd0.jpg'
  'https://tpsgsbxstorageaccount.blob.core.windows.net/tpsgsbxstoragecontainer/upload/7afaff13-edc2-4506-ad05-9ba537065641/6e8fa223-ca07-4b94-835b-4adde0ba7f0b.files?sv=2023-11-03&se=2124-11-02T14%3A28%3A24Z&sr=c&sp=r&sig=gpXzaFEwXqNNY14l%2BFXOwJSsSh0fXDKSLJqyPsiT1RA%3D'
    )
    print(res)
