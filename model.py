import requests
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Model:
    def __init__(self):
        self.metis_api_key = os.getenv('METIS_API_KEY')
        self.metis_endpoint = "https://api.metisai.ir/v1/wrapper/gpt-4o"  # Replace with the actual Metis API endpoint

    def analyze_image(self, image_path: str) -> List[Dict[str, str]]:
        """Send an image to GPT-4o through Metis wrapper API and get plant recommendations."""
        try:
            # Open the image file in binary mode
            with open(image_path, "rb") as image_file:
                # Prepare the request payload and headers for Metis API
                headers = {
                    "Authorization": f"Bearer {self.metis_api_key}",
                    "Content-Type": "multipart/form-data"
                }
                files = {
                    "file": image_file
                }
                data = {
                    "model": "gpt-4o",
                    "prompt": (
                        "1. *Analyze* the provided image to evaluate the lighting conditions and available space.\n"
                        "   - *Note:* If the image is other than place that a plant can be place in you should return {\"error\": \"badImage\", \"plants\":[] }.\n\n"
                        "2. *Recommend two suitable indoor plants* based on the following criteria:\n"
                        "   - Plants should not be rare and should be easy to find.\n"
                        "   - Only recommend plants suitable for *indoor* environments.\n"
                        "   - Ensure the plants are compatible with *Tehran's climate*.\n"
                        "   - Avoid any *illegal plants*, such as marijuana.\n"
                        "3. *Format your output in JSON*, ordered by relevance, with the following structure:\n"
                        "   - Each plant must include:\n"
                        "     - `scientificName`: the scientific name of the plant (in English).\n"
                        "     - `persianCommenName`: the common name plant is mostly known in Persian (in Farsi).\n"
                        "     - `description`: accurate care detail  (in Farsi).\n"
                        "     - `url`: a link to the image of this plant from internet\n"
                        "   - *Note:* Exclude any plants if any fields are empty or null.\n\n"
                        "*Example JSON Format:*\n"
                        "json\n"
                        "  {\n"
                        "  plants:\n"
                        "[\n"
                        "  {\n"
                        "    \"scientificName\": \"Ficus lyrata\",\n"
                        "    \"persianCommenName\": \"انجیر برگ‌ریز\"\n"
                        "    \"description\": \"فیکوس بنجامین درختچه‌ای زینتی با برگ‌های براق و کوچک است که در نور غیرمستقیم خورشید رشد می‌کند. نیاز به رطوبت متوسط و آبیاری منظم دارد. دمای مناسب بین ۱۶ تا ۲۴ درجه سانتیگراد است. از تغییرات ناگهانی دما و جریان مستقیم هوا باید محافظت شود.\"\n"
                        "    \"url\": \"https://www.greensouq.ae/wp-content/uploads/2018/10/1234.jpg\"\n"
                        "  },\n"
                        "  {\n"
                        "    \"scientificName\": \"Sansevieria trifasciata\",\n"
                        "    \"persianCommenName\": \"شمشیری\"\n"
                        "    \"description\": \"سانسوریا، معروف به زبان مادرشوهر، گیاهی مقاوم با برگ‌های بلند و ایستاده است که در شرایط نوری کم تا زیاد و با آبیاری کم، به‌خوبی رشد می‌کند. این گیاه در تصفیه هوای داخلی مؤثر است و به‌راحتی قابل نگهداری می‌باشد. به نور کم مقاوم است و به مراقبت خاصی نیاز ندارد.\"\n"
                        "    \"url\": \"https://peaceloveandhappiness.club/cdn/shop/files/succulents-cactus-sansevieria-asst-4-1.jpg?v=1693587149\"\n"
                        "  },\n"
                        "],\n\n"
                        "error: null\n"
                        "},\n"

                        "*Additional Note:* Sort the plants by relevance to the space and lighting conditions observed in the image."
                    ),
                    "max_tokens": 500,
                    "format": "application/json"  # Requesting JSON formatted response
                }

                # Send request to Metis API
                response = requests.post(self.metis_endpoint, headers=headers, files=files, data=data)

            # Check if response is successful
            if response.status_code == 200:
                plant_recommendations = response.json()  # Parse JSON response
                if plant_recommendations.error == 'badImage':
                    return [{"error": "Please more clear images of your space."}]
                if len(plant_recommendations.plants) == 0:
                    return [{"error": "Unable to retrieve plant recommendations at this time."}]

                return plant_recommendations

            # Handle unsuccessful response
            print(f"Error: Received response {response.status_code}")
            print(f"Response: {response.text}")
            return [{"error": "Unable to retrieve plant recommendations at this time."}]

        except Exception as e:
            print(f"Error fetching plant information from Metis API: {e}")
            return [{"error": "Unable to retrieve plant recommendations due to an error."}]
