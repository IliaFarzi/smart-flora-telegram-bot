import logging
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Iranian proxy settings
PROXY = {
    "http": "http://80.249.112.162:80",
    "https": "http://80.249.112.162:80"
}

class Model:
    def __init__(self):
        # Load API key from environment variable
        self.metis_api_key = os.getenv('METIS_API_KEY')
        self.storage_endpoint = "https://api.metisai.ir/api/v1/storage"  # Storage endpoint to upload image
        self.wrapper_endpoint = "https://api.metisai.ir/api/v1/wrapper/openai_chat_completion/chat/completions"  # Wrapper endpoint for image processing

    def upload_image(self, image_path: str) -> str:
        """Upload an image to Metis storage and return the URL."""
        try:
            with open(image_path, "rb") as image_file:
                headers = {"Authorization": f"Bearer {self.metis_api_key}"}
                files = {"file": image_file}

                # Send the request to upload the image through the proxy
                response = requests.post(self.storage_endpoint, headers=headers, files=files, proxies=PROXY)
                if response.status_code == 200:
                    image_url = response.json().get("url")
                    logger.info(f"Image uploaded successfully: {image_url}")
                    return image_url
                else:
                    logger.error(f"Image upload failed with status {response.status_code}: {response.text}")
                    return ""

        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            return ""

    def analyze_image(self, image_url: str):
        """Send the image URL to Metis API for plant analysis and get recommendations."""
        prompt = (
            "1. *Analyze* the provided image to evaluate the lighting conditions and available space.\n"
            "   - *Note:* If the image is other than a place where a plant can be placed, you should return {\"error\": \"badImage\", \"plants\":[] }.\n\n"
            "2. *Recommend two suitable indoor plants* based on the following criteria:\n"
            "   - Plants should not be rare and should be easy to find.\n"
            "   - Only recommend plants suitable for *indoor* environments.\n"
            "   - Ensure the plants are compatible with *Tehran's climate*.\n"
            "   - Avoid any *illegal plants*, such as marijuana.\n"
            "3. *Format your output in JSON*, ordered by relevance, with the following structure:\n"
            "   - Each plant must include:\n"
            "     - `scientificName`: the scientific name of the plant (in English).\n"
            "     - `persianCommenName`: the common name plant is mostly known in Persian (in Farsi).\n"
            "     - `description`: accurate care details (in Farsi).\n"
            "     - `url`: a link to the image of this plant from the internet\n"
            "   - *Note:* Exclude any plants if any fields are empty or null.\n\n"
            "*Example JSON Format:*\n"
            "{\n"
            "  \"plants\": [\n"
            "    {\n"
            "      \"scientificName\": \"Ficus lyrata\",\n"
            "      \"persianCommenName\": \"انجیر برگ‌ریز\",\n"
            "      \"description\": \"فیکوس بنجامین درختچه‌ای زینتی با برگ‌های براق و کوچک است که در نور غیرمستقیم خورشید رشد می‌کند. نیاز به رطوبت متوسط و آبیاری منظم دارد. دمای مناسب بین ۱۶ تا ۲۴ درجه سانتیگراد است. از تغییرات ناگهانی دما و جریان مستقیم هوا باید محافظت شود.\",\n"
            "      \"url\": \"https://www.greensouq.ae/wp-content/uploads/2018/10/1234.jpg\"\n"
            "    }\n"
            "  ],\n"
            "  \"error\": null\n"
            "}"
        )
        uploaded_image = self.upload_image(image_url)
        logger.info(uploaded_image)
        data = {
            "model": "gpt-4o",
            "prompt": prompt,
            "image_url": uploaded_image,
            "max_tokens": 500,
            "format": "application/json"
        }
        headers = {
            "Authorization": f"Bearer {self.metis_api_key}",
            "Content-Type": "application/json"
        }
        try:
            # Send the analysis request through the proxy
            response = requests.post(self.wrapper_endpoint, headers=headers, json=data, proxies=PROXY)

            if response.status_code == 200:
                response_data = response.json()

                # Check for error in the response
                if response_data.get("error") == "badImage":
                    return {"error": "Please provide clearer images of your space.", 'plants': []}
                elif not response_data.get("plants"):
                    return {"error": "No suitable plants found for the provided image.", 'plants': []}

                # Return list of plants if valid data is received
                return {"plants": response_data.get("plants", []), "error":"null"}
            else:
                logger.error(f"Error from Metis API: {response.status_code} - {response.text}")
                return {"error": "Unable to retrieve plant recommendations at this time.", 'plants': []}

        except Exception as e:
            logger.error(f"Error processing image with Metis API: {e}")
            return {'error': "Unable to retrieve plant recommendations due to an error.", 'plants': []}
