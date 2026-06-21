from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot.keyboards.inline import back_to_main_menu_button
from bot.config import Config
from sheets.sync import sync_all   # <-- импортируем нашу функцию

async def menu_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    sheets_url = f"https://docs.google.com/spreadsheets/d/{Config.SPREADSHEET_ID}"
    text = (
        "📊 Google Таблица\n\n"
        "Таблица обновляется автоматически при любых изменениях.\n"
        "Ручное редактирование запрещено — всё управление через бота.\n\n"
        f"<a href='{sheets_url}'>Открыть таблицу</a>"
    )
    keyboard = [
        [InlineKeyboardButton("🔄 Принудительно обновить", callback_data="sheets:sync")],
        back_to_main_menu_button()
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard),
                                  disable_web_page_preview=True)

async def force_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔄 Синхронизация запущена...")
    success = await sync_all()
    if success:
        await query.edit_message_text("✅ Синхронизация завершена. Таблица обновлена.")
    else:
        await query.edit_message_text("❌ Ошибка синхронизации. Проверьте настройки Google Sheets.")

def get_handlers():
    return [
        CallbackQueryHandler(menu_sheets, pattern="^menu:sheets$"),
        CallbackQueryHandler(force_sync, pattern="^sheets:sync$"),
    ]