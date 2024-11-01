import zipfile
import os
from PIL import Image

def convert_images_to_png(input_zip_path, output_zip_path):
    output_dir = 'MyFlower'
    os.makedirs(output_dir, exist_ok=True)

    # Unzip, convert to PNG, and save images
    with zipfile.ZipFile(input_zip_path, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            with zip_ref.open(file_name) as file:
                if file_name.lower().endswith(('.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')):
                    img = Image.open(file)
                    base_name = os.path.splitext(os.path.basename(file_name))[0]
                    output_file_path = os.path.join(output_dir, f"{base_name}.png")
                    img.save(output_file_path, format="PNG")

    # Zip the converted PNG files
    with zipfile.ZipFile(output_zip_path, 'w') as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)

    # Clean up temporary directory
    for file in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, file))
    os.rmdir(output_dir)

# Example usage
convert_images_to_png('flowers.zip', 'flowers_converted.zip')
