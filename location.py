from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Updater


# Function to ask the question and provide two options
def ask_question(update: Update, context: CallbackContext) -> None:
    question_text = "برای چه محیطی میخواید گلتون رو قرار بدین؟"
    options = [
        InlineKeyboardButton("سرباز", callback_data="outdoor"),
        InlineKeyboardButton("سرپوشیده", callback_data="indoor"),
    ]
    keyboard = InlineKeyboardMarkup([options])
    update.message.reply_text(question_text, reply_markup=keyboard)


# Callback to handle user's selection
def handle_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()  # Acknowledge the query
    selected_option = query.data  # This will be 'indoor' or 'outdoor'

    # Respond with the selected option in English
    if selected_option == "indoor":
        query.edit_message_text("You selected: Indoor")
    elif selected_option == "outdoor":
        query.edit_message_text("You selected: Outdoor")

