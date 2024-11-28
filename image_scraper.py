import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests


class ImageScraper:
    def __init__(self, driver_path="chromedriver"):
        self.driver_path = driver_path
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")

    def fetch_image(self, query: str, output_dir: str = "./images") -> str:
        """
        Fetches the first image for the given search query from Google Images.

        :param query: Search query (e.g., "Bougainvillea spectabilis")
        :param output_dir: Directory to save the image
        :return: Path to the downloaded image
        """
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        image_path = os.path.join(output_dir, f"{query.replace(' ', '_')}.jpg")

        # Start the WebDriver
        service = Service(self.driver_path)
        driver = webdriver.Chrome(service=service, options=self.chrome_options)

        try:
            # Open Google Images and search
            driver.get("https://images.google.com")
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(query)
            search_box.submit()

            time.sleep(2)  # Allow results to load

            # Locate the first image
            first_image = driver.find_element(By.CSS_SELECTOR, "img")
            image_url = first_image.get_attribute("src")

            # Download and save the image
            if image_url.startswith("http"):
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    with open(image_path, "wb") as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)
                else:
                    raise Exception("Failed to download image.")
            else:
                raise Exception("Image URL is not valid.")
        finally:
            driver.quit()

        return image_path