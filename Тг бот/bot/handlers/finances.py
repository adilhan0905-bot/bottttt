from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot.keyboards.inline import back_to_main_menu_button
from bot.services import db_interface as db


async def menu_finances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📊 По всем объектам", callback_data="fin:all")],
        [InlineKeyboardButton("🏗 По конкретному объекту", callback_data="fin:by_object")],
        back_to_main_menu_button()
    ]
    await query.edit_message_text("💰 Финансовая сводка:", reply_markup=InlineKeyboardMarkup(keyboard))


async def summary_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        data = await db.db_get_finance_summary(None)
    except NotImplementedError:
        data = {"total_labor": 0, "total_material_estimated": 0, "total_material_actual": 0, "total": 0}

    text = (
        f"💰 <b>Общие затраты по всем объектам</b>\n\n"
        f"Стоимость работ: {data['total_labor']:,.2f} руб.\n"
        f"Материалы (смета): {data['total_material_estimated']:,.2f} руб.\n"
        f"Материалы (факт): {data['total_material_actual']:,.2f} руб.\n"
        f"<b>ИТОГО:</b> {data['total']:,.2f} руб."
    )
    await query.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]))


def get_handlers():
    return [
        CallbackQueryHandler(menu_finances, pattern="^menu:finances$"),
        CallbackQueryHandler(summary_all, pattern="^fin:all$"),
        # TODO: [ТЫ] Добавить fin:by_object с выбором объекта и вызовом db_get_finance_summary(object_id)
    ]