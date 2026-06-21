from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, CommandHandler, filters
)

from bot.states import MaterialStates
from bot.keyboards.inline import cancel_button, back_to_main_menu_button, main_menu_keyboard
from bot.services import db_interface as db

async def menu_set_material_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💵 <b>Указать стоимость материалов</b>\n\n"
        "Эта функция позволяет задать базовые цены материалов в справочнике.\n"
        "Сейчас цены вводятся при создании каждой задачи.\n\n"
        "👋 Возврат в главное меню:",
        reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]),
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def cancel_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена с возвратом в главное меню"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Отменено.")
        from bot.handlers.start import main_menu_callback
        await main_menu_callback(update, context)
    else:
        await update.message.reply_text("❌ Отменено.")
        from bot.keyboards.inline import main_menu_keyboard
        await update.message.reply_text("👋 Главное меню:", reply_markup=main_menu_keyboard())

    context.user_data.pop("set_price_mat_id", None)
    return ConversationHandler.END

def get_handlers():
    return [
        CallbackQueryHandler(menu_set_material_prices, pattern="^menu:set:material_prices$"),
    ]