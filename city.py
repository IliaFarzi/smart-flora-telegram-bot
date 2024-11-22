from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from typing import List


# CityNames and CityNotFoundError
class CityNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)


class CityNames:
    def __init__(self):
        self.city_names =  {
            "Tehran": "تهران",          # Capital, Alborz Mountains
            "Isfahan": "اصفهان",        # Central Plateau
            "Shiraz": "شیراز",          # Zagros Mountains, near forests
            "Mashhad": "مشهد",          # Khorasan, biodiversity in Kopet Dag Mountains
            "Tabriz": "تبریز",          # East Azerbaijan, near volcanic Sahand
            "Ahvaz": "اهواز",           # Khuzestan, close to wetlands
            "Kerman": "کرمان",          # Lut Desert region
            "Rasht": "رشت",             # Caspian Sea, dense forests
            "Yazd": "یزد",              # Central Desert city
            "Bandar Abbas": "بندرعباس",  # Coastal biodiversity, Persian Gulf
            "Kish": "کیش",              # Biodiverse Persian Gulf island
            "Hamedan": "همدان",         # Alvand Mountains, historical sites
            "Qazvin": "قزوین",          # Near Alborz, fertile plains
            "Zahedan": "زاهدان",        # Sistan-Baluchestan, drylands
            "Sanandaj": "سنندج",        # Zagros Mountains
            "Khorramabad": "خرم‌آباد",  # Lorestan, valleys and caves
            "Ardabil": "اردبیل",        # Sabalan Mountains, mineral springs
            "Urmia": "ارومیه",          # Near Lake Urmia, diverse ecosystem
            "Gorgan": "گرگان",          # Caspian forests and Golestan National Park
            "Chabahar": "چابهار"        # Coastal city with mangroves
        }

    def get_en_name(self, farsi_name):
        reverse_city_names = {v: k for k, v in self.city_names.items()}
        if farsi_name not in reverse_city_names:
            raise CityNotFoundError(f"شهر '{farsi_name}' یافت نشد.")
        return reverse_city_names[farsi_name]

    def get_farsi_name(self, en_name):
        """Retrieve the Farsi name from the English name."""
        if en_name not in self.city_names:
            raise CityNotFoundError(f"City '{en_name}' not found.")
        return self.city_names[en_name]


# Instantiate CityNames
city_mapper = CityNames()


# Pagination function
def paginate(items: List[str], page: int, items_per_page: int = 10):
    start = page * items_per_page
    end = start + items_per_page
    return items[start:end], len(items) > end


# Start city selection
async def start_city_selection(update: Update, context: CallbackContext):
    page = 0
    farsi_cities = list(city_mapper.city_names.values())
    cities, has_next = paginate(farsi_cities, page)

    keyboard = [[InlineKeyboardButton(city, callback_data=f"select_city:{city}")] for city in cities]
    if has_next:
        keyboard.append([InlineKeyboardButton("Next", callback_data=f"city_page:{page + 1}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً شهر مورد نظر خود را انتخاب کنید:", reply_markup=reply_markup)


# Handle city pagination and selection
async def handle_city_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("city_page:"):
        page = int(data.split(":")[1])
        farsi_cities = list(city_mapper.city_names.values())
        cities, has_next = paginate(farsi_cities, page)

        keyboard = [[InlineKeyboardButton(city, callback_data=f"select_city:{city}")] for city in cities]
        if has_next:
            keyboard.append([InlineKeyboardButton("Next", callback_data=f"city_page:{page + 1}")])
        if page > 0:
            keyboard.append([InlineKeyboardButton("Previous", callback_data=f"city_page:{page - 1}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("لطفاً شهر مورد نظرتون رو انتخاب کنید:", reply_markup=reply_markup)

    elif data.startswith("select_city:"):
        farsi_name = data.split(":")[1]
        try:
            en_name = city_mapper.get_en_name(farsi_name)
            context.user_data['selected_city'] = en_name
            await query.edit_message_text(f"لطفاً یک عکس از فضای مورد نظرتون ارسال کنید.")
        except CityNotFoundError as e:
            await query.edit_message_text(str(e))
