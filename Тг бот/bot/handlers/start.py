from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from bot.config import Config
from bot.keyboards.inline import main_menu_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Добро пожаловать! Выберите действие:",
        reply_markup=main_menu_keyboard()
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню по callback_data."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👋 Главное меню. Выберите действие:",
        reply_markup=main_menu_keyboard()
    )


def get_handlers():
    return [
        CommandHandler("start", start_command),
        CallbackQueryHandler(main_menu_callback, pattern="^menu:main$"),
    ]