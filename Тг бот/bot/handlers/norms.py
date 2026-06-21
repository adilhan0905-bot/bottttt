from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, CommandHandler, filters
)

from bot.states import NormStates
from bot.keyboards.inline import work_types_list_keyboard, materials_list_keyboard, cancel_button, \
    back_to_main_menu_button
from bot.services import db_interface as db


async def menu_norms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("➕ Добавить / изменить норму", callback_data="norm:create")],
        [InlineKeyboardButton("📋 Посмотреть нормы по работе", callback_data="norm:view")],
        back_to_main_menu_button()
    ]
    await query.edit_message_text("📐 Нормы расхода материалов:", reply_markup=InlineKeyboardMarkup(keyboard))


async def start_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_norm"] = {}
    try:
        work_types = await db.db_get_all_work_types()
    except NotImplementedError:
        work_types = []
    if not work_types:
        await query.edit_message_text("Сначала добавьте типы работ.",
                                      reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]))
        return ConversationHandler.END
    await query.edit_message_text("Выберите тип работы:", reply_markup=work_types_list_keyboard(work_types, "norm:wt"))


async def select_work_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    wt_id = int(query.data.split(":")[2])
    context.user_data["new_norm"]["work_type_id"] = wt_id
    try:
        materials = await db.db_get_all_materials()
    except NotImplementedError:
        materials = []
    if not materials:
        await query.edit_message_text("Сначала добавьте материалы.",
                                      reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]))
        return ConversationHandler.END
    await query.edit_message_text("Выберите материал:", reply_markup=materials_list_keyboard(materials, "norm:mat"))
    return NormStates.SELECT_MATERIAL


async def select_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mat_id = int(query.data.split(":")[2])
    context.user_data["new_norm"]["material_id"] = mat_id
    await query.edit_message_text(
        "Введите количество материала на 1 единицу объёма работы (расходную норму):",
        reply_markup=InlineKeyboardMarkup([cancel_button()])
    )
    return NormStates.QUANTITY


async def receive_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qty = float(update.message.text.replace(",", ".").strip())
    except ValueError:
        await update.message.reply_text("❌ Введите число:", reply_markup=InlineKeyboardMarkup([cancel_button()]))
        return NormStates.QUANTITY

    context.user_data["new_norm"]["quantity_per_unit"] = qty
    n = context.user_data["new_norm"]
    # TODO: [ДРУГ] Можно подтянуть названия для красивого summary
    await update.message.reply_text(
        f"📋 Норма:\nРабота ID: {n['work_type_id']}\nМатериал ID: {n['material_id']}\nРасход: {n['quantity_per_unit']} на 1 ед.\n\nСохранить?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Сохранить", callback_data="norm:confirm"),
             InlineKeyboardButton("❌ Отмена", callback_data="dialog:cancel")]
        ])
    )
    return NormStates.CONFIRM


async def confirm_norm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    n = context.user_data.pop("new_norm", {})
    try:
        await db.db_set_norm(n["work_type_id"], n["material_id"], n["quantity_per_unit"])
        # TODO: [ИНТЕГРАЦИЯ] await db.db_trigger_sheets_sync("norm", n["work_type_id"])
        await query.edit_message_text("✅ Норма сохранена!")
    except NotImplementedError:
        await query.edit_message_text("⚠️ БД пока не подключена.")
    await menu_norms(update, context)
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

    context.user_data.pop("new_norm", None)
    return ConversationHandler.END


def get_handlers():
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_create, pattern="^norm:create$"),
        ],
        states={
            NormStates.SELECT_WORK_TYPE: [CallbackQueryHandler(select_work_type, pattern="^norm:wt:\\d+$")],
            NormStates.SELECT_MATERIAL: [CallbackQueryHandler(select_material, pattern="^norm:mat:\\d+$")],
            NormStates.QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity)],
            NormStates.CONFIRM: [CallbackQueryHandler(confirm_norm, pattern="^norm:confirm$")],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_dialog, pattern="^dialog:cancel$"),
            CommandHandler("cancel", cancel_dialog),
        ],
    )
    return [
        CallbackQueryHandler(menu_norms, pattern="^menu:norms$"),
        conv,
    ]