import openai
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Model:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def analyze_image(self, image_path: str) -> Dict[str, str]:
        """Send an image to GPT-4 and get plant information"""
        try:
            # Open the image file in binary mode
            with open(image_path, "rb") as image_file:
                # Hypothetical image processing API call to GPT-4 with vision capabilities
                response = openai.Image.create(
                    model="gpt-4-vision",  # Hypothetical model name
                    file=image_file,
                    prompt=(
                        "Identify the plant in the image and provide the following details:\n"
                        "1. Scientific name of the plant.\n"
                        "2. Common name of the plant.\n"
                        "3. A short description including any interesting facts.\n"
                    ),
                    max_tokens=150
                )

            # Parsing GPT-4 response
            plant_info = response.choices[0].text.strip().split("\n")
            info_dict = {
                "scientific_name": plant_info[0].replace("Scientific Name:", "").strip(),
                "common_name": plant_info[1].replace("Common Name:", "").strip(),
                "description": plant_info[2].replace("Description:", "").strip()
            }
            return info_dict

        except Exception as e:
            print(f"Error fetching plant information from GPT-4: {e}")
            return {"error": "Unable to identify the plant. Please try again later."}
