import logging
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from pathlib import Path
import os
from dotenv import load_dotenv
from model import MetisUploader, MetisSuggestion
from city import start_city_selection, handle_city_selection, city_mapper
from iran_time import IranTime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

iran_time = IranTime()


# Configuration
class Config:
    TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
    TEMP_DIR: Path = Path('uploads')
    PUBLIC_DIR: Path = Path('public')
    TEMP_DIR.mkdir(exist_ok=True)  # Ensure temp directory exists
    DEFAULT_IMAGE_PATH = Path('public') / "default.png"


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
            "من بهترین پیشنهادها رو براتون آماده می‌کنم! 🪴")
        await update.message.reply_text(welcome_message)
        await start_city_selection(update, context)


    async def city_change_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /city_hange command"""
        await start_city_selection(update, context)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle received photos"""
        # Check if the user has selected a city
        if 'selected_city' not in context.user_data:
            await update.message.reply_text("❌ لطفاً شهرتون انتخاب کنید!")
            await start_city_selection(update, context)
            return

        try:
            # Download the user's photo
            photo = update.message.photo[-1]  # Get the highest resolution photo
            file = await photo.get_file()
            file_path = config.TEMP_DIR / f"{file.file_id}.jpg"
            await file.download_to_drive(file_path)

            # Store the file path temporarily in user data
            context.user_data['uploaded_file_path'] = file_path

            # Prompt user for indoor/outdoor selection
            await self.ask_environment_choice(update, context)

        except Exception as e:
            logger.error(f"Error in handle_photo: {e}")
            await update.message.reply_text(
                "❌ متأسفانه خطایی رخ داده\n"
                "🙏 لطفاً دوباره تلاش کنید"
            )

    async def ask_environment_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Prompt the user to choose between indoor and outdoor."""
        question = "فضای مد نظرتون رو انتخاب کنید:"
        options = [
            InlineKeyboardButton("سرباز", callback_data="environment:outdoor"),
            InlineKeyboardButton("سرپوشیده", callback_data="environment:indoor"),
        ]
        keyboard = InlineKeyboardMarkup([options])
        await update.message.reply_text(question, reply_markup=keyboard)

    async def handle_environment_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the user's choice for environment."""
        query = update.callback_query
        await query.answer()  # Acknowledge the callback

        # Extract the choice
        choice = query.data.split(":")[1]  # "outdoor" or "indoor"
        context.user_data['environment'] = choice

        # Log the user's choice
        logger.info(f"User selected environment: {choice}")

        # Confirm the choice
        await query.edit_message_text(
            f"✅ انتخاب شما: {'سرباز' if choice == 'outdoor' else 'سرپوشیده'}"
        )

        # Notify the user and proceed with image analysis
        selected_city = context.user_data['selected_city']
        await query.message.reply_text(
            f"شهر انتخابی شما: {city_mapper.get_farsi_name(selected_city)}\n⏳ در حال پردازش تصویر شما..."
        )
        await self.analyze_uploaded_image(query.message, context)

    async def analyze_uploaded_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Analyze the uploaded image based on user inputs."""
        try:
            file_path = context.user_data.get('uploaded_file_path')
            environment = context.user_data.get('environment')
            selected_city = context.user_data.get('selected_city')

            if not file_path or not environment:
                raise ValueError("Missing file or environment information.")

            # Upload the file
            uploaded_path = self.uploader_service.upload_file(str(file_path))

            if not uploaded_path:
                await update.message.reply_text("❌ متأسفانه در آپلود تصویر مشکلی پیش آمده\n🙏 لطفاً دوباره تلاش کنید")
                return

            # Use the API to analyze the image and get plant info
            plants_info = self.recommendation_service.analyze_image(uploaded_path, selected_city,
                                                                    iran_time.get_current_hour_am_pm(),
                                                                    iran_time.get_current_month_name(), )

            if plants_info['error'] is not None:
                raise Exception(plants_info['error'])

            # Prepare the caption for the default image
            for item in plants_info['plants']:
                response_message = (
                    f"🪴 اطلاعات گیاه پیشنهادی:\n"
                    f"📚 نام علمی: {item['scientificName']}\n"
                    f"🌿 نام فارسی: {item['persianCommonName']}\n"
                    f"📝 توضیحات: {item['description']}"
                )
                # Send the default image with the plant info as the caption
                if config.DEFAULT_IMAGE_PATH.exists():
                    with config.DEFAULT_IMAGE_PATH.open("rb") as image_file:  # Open the file in binary mode
                        await update.message.reply_photo(
                            photo=InputFile(image_file),
                            caption=response_message
                        )
                else:
                    await update.message.reply_text(response_message)

        except Exception as e:
            logger.error(f"Error in handle_photo: {e}")
            await update.message.reply_text(
                "❌ متأسفانه خطایی رخ داده\n"
                "🙏 لطفاً دوباره تلاش کنید"
            )
        finally:
            # Clean up the temporary file
            if 'file_path' in locals():
                file_path.unlink(missing_ok=True)

            # Ensure that the bot is ready for the next interaction (commands or messages)
            await update.message.reply_text("🛠️ آماده دریافت دستور جدید.")


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
        app.add_handler(CommandHandler("city", bot.city_change_command))
        app.add_handler(CallbackQueryHandler(handle_city_selection, pattern="^(city_page:|select_city:)"))
        app.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
        app.add_handler(CallbackQueryHandler(bot.handle_environment_choice, pattern="^environment:"))
        app.add_error_handler(error_handler)

        # Start the bot
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Critical error starting bot: {e}")
        print(f"Critical error starting bot: {e}")


if __name__ == '__main__':
    main()
