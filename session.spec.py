import os
import requests
import json
from dotenv import load_dotenv


load_dotenv()
# Load API key from environment variable
METIS_API_KEY = os.getenv("METIS_API_KEY")
METIS_BOT_ID = os.getenv("METIS_BOT_ID")

if not METIS_API_KEY:
    raise ValueError("API Key not found. Please set the METIS_API_KEY environment variable.")

# Define the request URL and headers
url = "https://api.metisai.ir/api/v1/chat/session"
headers = {
    "Authorization": f"Bearer {METIS_API_KEY}",
    "Content-Type": "application/json"
}

prompt = (
    "According to the image's provided in next prompts lighting conditions and available space, "
    "recommend two indoor plants based on these criteria:\n"
    "1. Plants should be easy to find and not rare.\n"
    "2. Plants should be suitable for indoor environments and compatible with Tehran's climate.\n"
    "3. Avoid recommending any illegal plants.\n\n"
    "Output in JSON format with the following structure:\n"
    "   - *Note:* If the image is other than a place where a plant can be placed, you should return {\"error\": \"badImage\", \"plants\":[] }.\n\n"
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

# Define the request payload
payload = {
    "botId": METIS_BOT_ID,  # Replace BOT_ID with your bot's ID
    "user": None,
    "initialMessages": [
        {
            "type": "USER",
            "content": prompt
        }
    ]
}

# Send the request
try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # Raise an exception for HTTP errors
    data = response.json()
    print("Response from Metis API:", data)
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
