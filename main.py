import random
from typing import Dict, List, Optional

import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import os
from dotenv import load_dotenv
from pathlib import Path
from dataclasses import dataclass
import logging
import asyncio

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Configuration
@dataclass
class Config:
    TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
    FLOWERS_DIR: Path = Path('images')
    CSV_FILE: Path = Path('plants.csv')
    VALID_EXTENSIONS: set = frozenset({'.jpg', '.jpeg', '.png'})


config = Config()


class PlantDatabase:
    def __init__(self):
        self.plants: Dict[str, dict] = {}
        self.load_database()

    def load_database(self) -> None:
        """Load plant information from CSV file"""
        try:
            if not config.CSV_FILE.exists():
                logger.error(f"CSV file not found: {config.CSV_FILE}")
                return

            # Load CSV data
            df = pd.read_csv(config.CSV_FILE)
            for _, row in df.iterrows():
                if pd.notna(row['Scientific Name']):
                    scientific_name = str(row['Scientific Name']).strip().lower()
                    self.plants[scientific_name] = {
                        'persian_name': str(row['Persian Name']) if pd.notna(
                            row['Persian Name']) else "نام فارسی موجود نیست",
                        'description': str(row['Description']) if pd.notna(row['Description']) else "توضیحات موجود نیست"
                    }
            logger.info(f"Loaded {len(self.plants)} plants from CSV")
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")

    def get_plant_info(self, filename: str, number: int) -> str:
        """Get plant information based on filename"""
        try:
            scientific_name = filename.split('.')[0].replace('_', ' ').lower()

            # Direct match
            if scientific_name in self.plants:
                return self._format_plant_info(scientific_name, self.plants[scientific_name], number)

            # Partial match
            for db_name, info in self.plants.items():
                if scientific_name in db_name or db_name in scientific_name:
                    return self._format_plant_info(db_name, info, number)

            return f"🌱 گیاه شماره {number}:\n{filename}\nاطلاعات این گیاه در دیتابیس موجود نیست."
        except Exception as e:
            logger.error(f"Error getting plant info: {e}")
            return f"🌱 گیاه شماره {number}:\n{filename}\nخطا در بازیابی اطلاعات"

    @staticmethod
    def _format_plant_info(scientific_name: str, info: dict, number: int) -> str:
        return (
            f"🌱 گیاه شماره {number}:\n"
            f"📚 نام علمی: {scientific_name.title()}\n"
            f"🇮🇷 نام فارسی: \u200F{info['persian_name']}\n"
            f"🗒 توضیحات: \u200F{info['description']}"
        )


class FlowerBot:
    def __init__(self):
        self.plant_db = PlantDatabase()
        self.flowers_dir = config.FLOWERS_DIR

    def get_flower_photos(self) -> List[str]:
        """Get list of all flower photos from the local directory"""
        try:
            if not self.flowers_dir.exists():
                logger.error(f"Flowers directory not found: {self.flowers_dir}")
                return []

            return [
                file.name for file in self.flowers_dir.iterdir()
                if file.suffix.lower() in config.VALID_EXTENSIONS
            ]
        except Exception as e:
            logger.error(f"Error reading flower directory: {e}")
            return []

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command"""
        welcome_message = (
            "🌸 به ربات پیشنهاد گیاه خوش آمدید! 🌸\n\n"
            "یک عکس برای من بفرستید تا دو گیاه زیبا به شما پیشنهاد دهم!"
        )
        await update.message.reply_text(welcome_message)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle received photos"""
        try:
            flower_files = self.get_flower_photos()
            if len(flower_files) < 3:
                await update.message.reply_text("تعداد گیاه‌های موجود در مجموعه کافی نیست!")
                return

            await update.message.reply_text("✨ گیاه‌های پیشنهادی من برای شما: ✨")

            selected_flowers = random.sample(flower_files, 2)
            for i, flower in enumerate(selected_flowers, 1):
                file_path = self.flowers_dir / flower
                caption = self.plant_db.get_plant_info(flower, i)

                try:
                    # Introduce a random delay between 3 and 7 seconds before sending each image
                    await asyncio.sleep(random.uniform(2, 5))
                    with open(file_path, 'rb') as photo_file:
                        await update.message.reply_photo(photo=photo_file, caption=caption)
                except Exception as e:
                    logger.error(f"Error sending photo {flower}: {e}")
                    await update.message.reply_text(f"خطا در ارسال عکس {flower}")

            await update.message.reply_text("امیدوارم این پیشنهادات برای شما مفید باشد! 🌺")

        except Exception as e:
            logger.error(f"Error in handle_photo: {e}")
            await update.message.reply_text(
                "متأسفانه در نمایش گیاه‌ها مشکلی پیش آمد. لطفاً دوباره تلاش کنید!"
            )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text("متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    except:
        pass


def main() -> None:
    """Main function to run the bot"""
    try:
        # Initialize the bot
        bot = FlowerBot()
        app = (Application.builder().pool_timeout(1200).read_timeout(1200).write_timeout(1200).connect_timeout(1200)
               ).token(config.TELEGRAM_TOKEN).build()

        # Add handlers
        app.add_handler(CommandHandler("start", bot.start_command))
        app.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
        app.add_error_handler(error_handler)

        # Print startup information
        print("در حال شروع ربات پیشنهاد گیاه...")
        print(f"مسیر پوشه گیاه‌ها: {config.FLOWERS_DIR}")
        print(f"مسیر فایل CSV: {config.CSV_FILE}")
        print(f"تعداد گیاهان در دیتابیس: {len(bot.plant_db.plants)}")
        print(f"تعداد عکس‌های گیاه: {len(bot.get_flower_photos())}")

        # Start the bot
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info(config.TELEGRAM_TOKEN)
    except Exception as e:
        logger.critical(f"Critical error starting bot: {e}")
        print(f"خطای بحرانی در اجرای ربات: {e}")


if __name__ == '__main__':
    main()
