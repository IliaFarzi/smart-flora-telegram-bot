import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pathlib import Path
import os
from dotenv import load_dotenv
from model import MetisUploader, MetisSuggestion

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
    TEMP_DIR: Path = Path('uploads')
    PUBLIC_DIR: Path = Path('public')
    TEMP_DIR.mkdir(exist_ok=True)  # Ensure temp directory exists

config = Config()

class FlowerBot:
    def __init__(self):
        self.recommendation_service = MetisSuggestion()
        self.uploader_service = MetisUploader()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command"""
        welcome_message = (
            "🌸 Welcome to the Plant Recommendation Bot! 🌸\n\n"
            "Send me a photo of a plant, and I'll try to identify it and provide interesting details!"
        )
        await update.message.reply_text(welcome_message)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle received photos"""
        try:
            # Download the user's photo
            photo = update.message.photo[-1]  # Get the highest resolution photo
            file = await photo.get_file()
            file_path = config.TEMP_DIR / f"{file.file_id}.jpg"
            await file.download_to_drive(file_path)
            uploaded_path = self.uploader_service.upload_file(str(file_path))

            # Use GPT-4 to analyze the image and get plant info
            plants_info = self.recommendation_service.analyze_image(uploaded_path)
            if "error" in plants_info and plants_info["error"] != "null":
                await update.message.reply_text(plants_info["error"])
            else:
                # Prepare the caption for the default image
                captions = []
                for item in plants_info['plants']:
                    response_message = (
                        f"🌱 Plant Information:\n"
                        f"📚 Scientific Name: {item['scientificName']}\n"
                        f"🇮🇷 Common Name: {item['persianCommonName']}\n"
                        f"🗒 Description: {item['description']}"
                    )
                    captions.append(response_message)

                # Send the default image with the plant info as the caption
                default_image_path = config.PUBLIC_DIR / "default.png"
                if default_image_path.exists():
                    await update.message.reply_photo(photo=InputFile(default_image_path), caption="\n\n".join(captions))

            # Optionally delete the image after processing
            file_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error in handle_photo: {e}")
            await update.message.reply_text(
                "متاسفانه خطایی رخ داده"
            )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text("An error occurred. Please try again.")
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

def main() -> None:
    """Main function to run the bot"""
    try:
        # Initialize the bot
        bot = FlowerBot()
        app = (Application.builder()
               .token(config.TELEGRAM_TOKEN)
               .build())

        # Add handlers
        app.add_handler(CommandHandler("start", bot.start_command))
        app.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
        app.add_error_handler(error_handler)

        # Start the bot
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Critical error starting bot: {e}")
        print(f"Critical error starting bot: {e}")

if __name__ == '__main__':
    main()
