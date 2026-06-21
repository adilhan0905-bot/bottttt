from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from bot.states import ObjectStates
from bot.keyboards.inline import (
    objects_list_keyboard, confirm_cancel_row, back_to_main_menu_button, cancel_button
)
from bot.services import db_interface as db


# Временное хранилище данных диалога в context.user_data["new_object"]
async def menu_objects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # TODO: [ДРУГ] db.db_get_all_objects() — пока заглушка, ловим ошибку
    try:
        objects = await db.db_get_all_objects()
    except NotImplementedError:
        objects = []

    text = "🏗 Объекты строительства:\n\n"
    if not objects:
        text += "Список пуст. Нажмите «Добавить объект»."
    else:
        for obj in objects:
            ext = f" (ID: {obj['external_id']})" if obj.get('external_id') else ""
            text += f"• {obj['name']}{ext} — {obj.get('address', 'нет адреса')}\n"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить объект", callback_data="obj:create")],
        back_to_main_menu_button()
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def start_create_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_object"] = {}
    await query.edit_message_text("Введите название объекта:", reply_markup=InlineKeyboardMarkup([cancel_button()]))
    return ObjectStates.NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_object"]["name"] = update.message.text.strip()
    await update.message.reply_text("Введите адрес объекта:", reply_markup=InlineKeyboardMarkup([cancel_button()]))
    return ObjectStates.ADDRESS


async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_object"]["address"] = update.message.text.strip()
    await update.message.reply_text(
        "Введите внешний ID (опционально). Если не нужен — отправьте «-»:",
        reply_markup=InlineKeyboardMarkup([cancel_button()])
    )
    return ObjectStates.EXTERNAL_ID


async def receive_external_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["new_object"]["external_id"] = None if text == "-" else text

    obj = context.user_data["new_object"]
    summary = f"📋 Проверьте данные:\n\nНазвание: {obj['name']}\nАдрес: {obj['address']}\nВнешний ID: {obj.get('external_id') or 'нет'}"
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup([confirm_cancel_row()]))
    return ObjectStates.CONFIRM


async def confirm_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    obj = context.user_data.pop("new_object", {})

    # TODO: [ДРУГ] Сохранение в БД + синхронизация Google Sheets
    try:
        created = await db.db_create_object(obj["name"], obj["address"], obj.get("external_id"))
        # TODO: [ИНТЕГРАЦИЯ] await db.db_trigger_sheets_sync("object", created["id"])
        await query.edit_message_text(f"✅ Объект «{created['name']}» создан!")
    except NotImplementedError:
        await query.edit_message_text("⚠️ Сохранение пока не работает (друг не подключил БД).")

    # Возврат в меню объектов
    await menu_objects(update, context)
    return ConversationHandler.END


async def cancel_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена с возвратом в главное меню"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Операция отменена.")
        from bot.handlers.start import main_menu_callback
        await main_menu_callback(update, context)
    else:
        await update.message.reply_text("❌ Операция отменена.")
        from bot.keyboards.inline import main_menu_keyboard
        await update.message.reply_text("👋 Главное меню:", reply_markup=main_menu_keyboard())

    context.user_data.pop("new_object", None)
    return ConversationHandler.END


def get_handlers():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup  # локальный импорт для кнопок

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_create_object, pattern="^obj:create$")],
        states={
            ObjectStates.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            ObjectStates.ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
            ObjectStates.EXTERNAL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_external_id)],
            ObjectStates.CONFIRM: [CallbackQueryHandler(confirm_object, pattern="^dialog:confirm$")],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_dialog, pattern="^dialog:cancel$"),
            CommandHandler("cancel", cancel_dialog),
        ],
    )

    return [
        CallbackQueryHandler(menu_objects, pattern="^menu:objects$"),
        conv,
    ]