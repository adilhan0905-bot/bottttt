from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, CommandHandler, filters
)

from bot.states import PurchaseStates
from bot.keyboards.inline import tasks_list_keyboard, purchase_status_keyboard, back_to_main_menu_button
from bot.services import db_interface as db


async def menu_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📋 По задаче", callback_data="purchase:by_task")],
        [InlineKeyboardButton("📦 Общий список закупок", callback_data="purchase:shopping_list")],
        back_to_main_menu_button()
    ]
    await query.edit_message_text("🛒 Управление закупками:", reply_markup=InlineKeyboardMarkup(keyboard))


async def by_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        tasks = await db.db_get_tasks_by_object()
    except NotImplementedError:
        tasks = []
    if not tasks:
        await query.edit_message_text("Нет задач.", reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]))
        return ConversationHandler.END
    await query.edit_message_text("Выберите задачу:", reply_markup=tasks_list_keyboard(tasks, "purchase:task"))


async def select_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[2])
    context.user_data["purchase_task_id"] = task_id

    try:
        task = await db.db_get_task_by_id(task_id)
    except NotImplementedError:
        task = None

    if not task:
        await query.edit_message_text("Задача не найдена.",
                                      reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]))
        return ConversationHandler.END

    text = f"📝 Задача #{task['id']}\nМатериалы:\n\n"
    for tm in task.get("materials", []):
        status = "✅ Закуплено" if tm.get("is_purchased") else "❌ Не закуплено"
        actual = f", факт: {tm['actual_cost']} руб" if tm.get("actual_cost") else ""
        text += f"• {tm['name']}: {tm['final_qty']} {tm['unit']} — {status}{actual}\n"

    # Кнопка "Отметить всё закупленным"
    keyboard = [
        [InlineKeyboardButton("✅ Всё закуплено", callback_data=f"purchase:all:{task_id}")],
        back_to_main_menu_button()
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return PurchaseStates.SELECT_MATERIAL


async def toggle_all_purchased(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[2])
    try:
        await db.db_set_task_all_purchased(task_id, True)
        await query.edit_message_text("✅ Все материалы отмечены как закупленные.")
    except NotImplementedError:
        await query.edit_message_text("⚠️ БД не подключена.")
    await menu_purchases(update, context)
    return ConversationHandler.END


async def shopping_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        items = await db.db_get_shopping_list()
    except NotImplementedError:
        items = []

    if not items:
        await query.edit_message_text("Все материалы закуплены или задач нет.",
                                      reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]))
        return

    text = "📦 Сводный список закупок:\n\n"
    for i in items:
        text += f"• {i['name']}: {i['total_qty']:,.2f} {i['unit']} (≈{i.get('estimated_cost', 0):,.2f} руб)\n"

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]))


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

    context.user_data.pop("purchase_task_id", None)
    return ConversationHandler.END


def get_handlers():
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(by_task_start, pattern="^purchase:by_task$")],
        states={
            PurchaseStates.SELECT_TASK: [CallbackQueryHandler(select_task, pattern="^purchase:task:\\d+$")],
            PurchaseStates.SELECT_MATERIAL: [
                # Здесь можно добавить хендлеры на отметку отдельного материала
                CallbackQueryHandler(toggle_all_purchased, pattern="^purchase:all:\\d+$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_dialog, pattern="^dialog:cancel$"),
            CommandHandler("cancel", cancel_dialog),
        ],
    )
    return [
        CallbackQueryHandler(menu_purchases, pattern="^menu:purchases$"),
        CallbackQueryHandler(shopping_list, pattern="^purchase:shopping_list$"),
        CallbackQueryHandler(toggle_all_purchased, pattern="^purchase:all:\\d+$"),
        conv,
    ]