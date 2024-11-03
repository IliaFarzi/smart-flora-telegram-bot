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
            "🌸 به ربات پیشنهاد گیاهان خوش آمدید! 🌸\n\n"
            "🌿 کافیه یک عکس از فضای مورد نظرتون برای قرار دادن گیاه ارسال کنید\n"
            "من بهترین پیشنهادها رو براتون آماده می‌کنم! 🪴"
        )
        await update.message.reply_text(welcome_message)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle received photos"""
        # Send waiting message
        waiting_message = await update.message.reply_text(
            "🔍 در حال بررسی تصویر و انتخاب بهترین گیاهان مناسب...\n"
            "🙏 لطفاً کمی صبر کنید"
        )

        try:
            # Download the user's photo
            photo = update.message.photo[-1]  # Get the highest resolution photo
            file = await photo.get_file()
            file_path = config.TEMP_DIR / f"{file.file_id}.jpg"
            await file.download_to_drive(file_path)
            uploaded_path = self.uploader_service.upload_file(str(file_path))

            if not uploaded_path:
                await waiting_message.edit_text("❌ متأسفانه در آپلود تصویر مشکلی پیش آمده\n🙏 لطفاً دوباره تلاش کنید")
                return

            # Use the API to analyze the image and get plant info
            plants_info = self.recommendation_service.analyze_image(uploaded_path)

            if plants_info.get("error"):
                error_messages = {
                    "Invalid response format": "❌ متأسفانه در پردازش تصویر مشکلی پیش آمده\n🙏 لطفاً دوباره تلاش کنید",
                    "Please provide clearer images of your space": "📸 لطفاً یک تصویر واضح‌تر از فضای مورد نظر ارسال کنید",
                    "Unable to retrieve plant recommendations at this time": "⚠️ در حال حاضر سیستم قادر به پاسخگویی نیست\n🙏 لطفاً دقایقی دیگر تلاش کنید",
                    "An unexpected error occurred during processing": "❌ متأسفانه خطایی رخ داده\n🙏 لطفاً دوباره تلاش کنید"
                }
                await waiting_message.edit_text(
                    error_messages.get(plants_info["error"], "❌ متأسفانه خطایی رخ داده\n🙏 لطفاً دوباره تلاش کنید"))
                return

            if not plants_info.get("plants"):
                await waiting_message.edit_text(
                    "⚠️ متأسفانه نتوانستم گیاه مناسبی برای این فضا پیدا کنم\n🌱 لطفاً تصویر دیگری ارسال کنید")
                return

            # Delete waiting message
            await waiting_message.delete()

            # Prepare the caption for the default image
            captions = []
            for item in plants_info['plants']:
                response_message = (
                    f"🪴 اطلاعات گیاه پیشنهادی:\n"
                    f"📚 نام علمی: {item['scientificName']}\n"
                    f"🌿 نام فارسی: {item['persianCommonName']}\n"
                    f"📝 توضیحات: {item['description']}"
                )
                captions.append(response_message)

            # Send the default image with the plant info as the caption
            default_image_path = config.PUBLIC_DIR / "default.png"
            if default_image_path.exists():
                await update.message.reply_photo(
                    photo=InputFile(default_image_path),
                    caption="\n\n" + "➖" * 20 + "\n\n".join(captions)
                )
            else:
                await update.message.reply_text("\n\n" + "➖" * 20 + "\n\n".join(captions))

        except Exception as e:
            logger.error(f"Error in handle_photo: {e}")
            await waiting_message.edit_text(
                "❌ متأسفانه خطایی رخ داده\n"
                "🙏 لطفاً دوباره تلاش کنید"
            )
        finally:
            # Clean up the temporary file
            if 'file_path' in locals():
                file_path.unlink(missing_ok=True)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داده\n"
            "🙏 لطفاً دوباره تلاش کنید"
        )
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