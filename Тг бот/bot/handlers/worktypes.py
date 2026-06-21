from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, CommandHandler, filters
)

from bot.states import SetPriceStates
from bot.keyboards.inline import work_types_list_keyboard, cancel_button, back_to_main_menu_button, main_menu_keyboard
from bot.services import db_interface as db


async def menu_set_labor_costs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        items = await db.db_get_all_work_types()
    except Exception:
        items = []
    if not items:
        await query.edit_message_text("Справочник типов работ пуст.",
                                      reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()]))
        return ConversationHandler.END

    text = "🔨 <b>Указать стоимость работы за каждый тип работы</b>\n\nВыберите тип работы:\n"
    keyboard = []
    for i in items:
        cost_str = f"{i['labor_cost_per_unit']} руб/м²" if i.get('labor_cost_per_unit') else "не задана"
        text += f"• {i['name']} — {cost_str}\n"
        keyboard.append([InlineKeyboardButton(
            f"✏️ {i['name']} ({cost_str})", callback_data=f"setcost:wt:{i['id']}"
        )])
    keyboard.append(back_to_main_menu_button())

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return SetPriceStates.SELECT_WORK_TYPE_COST


async def select_work_type_for_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    wt_id = int(query.data.split(":")[2])
    context.user_data["set_cost_wt_id"] = wt_id

    try:
        items = await db.db_get_all_work_types()
        wt = next((w for w in items if w["id"] == wt_id), None)
    except Exception:
        wt = None

    name = wt["name"] if wt else "тип работы"
    current = wt["labor_cost_per_unit"] if wt and wt.get("labor_cost_per_unit") else "не задана"

    await query.edit_message_text(
        f"🔨 {name}\nТекущая стоимость: {current} руб/м²\n\nВведите новую стоимость (руб/м²):",
        reply_markup=InlineKeyboardMarkup([cancel_button()])
    )
    return SetPriceStates.INPUT_WORK_TYPE_COST


async def save_work_type_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cost = float(update.message.text.replace(",", ".").strip())
    except ValueError:
        await update.message.reply_text("❌ Введите число:", reply_markup=InlineKeyboardMarkup([cancel_button()]))
        return SetPriceStates.INPUT_WORK_TYPE_COST

    wt_id = context.user_data.pop("set_cost_wt_id", None)
    if wt_id is None:
        await update.message.reply_text("❌ Ошибка. Попробуйте снова.")
        return ConversationHandler.END

    try:
        await db.db_update_work_type_cost(wt_id, cost)
        await update.message.reply_text("✅ Стоимость работы обновлена!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {e}")

    await update.message.reply_text("👋 Главное меню:", reply_markup=main_menu_keyboard())
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

    context.user_data.pop("set_cost_wt_id", None)
    return ConversationHandler.END


def get_handlers():
    conv = ConversationHandler(
        per_message=True,
        entry_points=[CallbackQueryHandler(menu_set_labor_costs, pattern="^menu:set:labor_costs$")],
        states={
            SetPriceStates.SELECT_WORK_TYPE_COST: [
                CallbackQueryHandler(select_work_type_for_cost, pattern="^setcost:wt:\\d+$")
            ],
            SetPriceStates.INPUT_WORK_TYPE_COST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_work_type_cost)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_dialog, pattern="^dialog:cancel$"),
            CommandHandler("cancel", cancel_dialog),
        ],
    )
    return [conv]