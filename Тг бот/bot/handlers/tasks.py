import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, CommandHandler, filters
)

from bot.states import TaskStates
from bot.keyboards.inline import (
    network_select_keyboard, work_types_list_keyboard, cancel_button, back_to_main_menu_button
)
from bot.services import db_interface as db
from bot.services import calc_service
from sheets.sync import sync_all

logger = logging.getLogger(__name__)


# ===================== HANDLERS =====================

async def start_create_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_task"] = {}
    await query.edit_message_text(
        "🏗 <b>Добавление объекта</b>\n\nВыберите сеть:",
        reply_markup=network_select_keyboard(),
        parse_mode="HTML"
    )
    return TaskStates.SELECT_NETWORK


async def select_network(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    network = query.data.split(":")[1]
    context.user_data["new_task"]["network"] = network

    # Удаляем сообщение с кнопками
    await query.delete_message()

    # Отправляем новое сообщение с просьбой ввести адрес
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Выбрана сеть: <b>{network}</b>\n\nВведите адрес объекта:",
        reply_markup=InlineKeyboardMarkup([cancel_button()]),
        parse_mode="HTML"
    )
    return TaskStates.INPUT_ADDRESS


async def input_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    nt = context.user_data["new_task"]
    nt["address"] = address

    print(f"[input_address] Адрес: {address}")

    # Создаём объект в БД
    try:
        obj = await db.db_create_object(
            name=address,
            address=address,
            network=nt["network"]
        )
        nt["object_id"] = obj["id"]
        print(f"[input_address] Объект создан: {obj}")
    except Exception as e:
        print(f"[input_address] Ошибка создания объекта: {e}")
        await update.message.reply_text(
            f"❌ Ошибка создания объекта: {e}",
            reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()])
        )
        return ConversationHandler.END

    # Получаем типы работ
    try:
        work_types = await db.db_get_all_work_types()
        print(f"[input_address] Получено типов работ: {len(work_types)}")
    except Exception as e:
        print(f"[input_address] Ошибка получения типов работ: {e}")
        work_types = []

    if not work_types:
        await update.message.reply_text(
            "❌ Нет типов работ в справочнике. Запустите python db/seed_data.py",
            reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()])
        )
        return ConversationHandler.END

    # Формируем клавиатуру
    try:
        keyboard = work_types_list_keyboard(work_types, "task:wt")
        print("[input_address] Клавиатура сформирована")
    except Exception as e:
        print(f"[input_address] Ошибка формирования клавиатуры: {e}")
        await update.message.reply_text(
            f"❌ Ошибка формирования клавиатуры: {e}",
            reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()])
        )
        return ConversationHandler.END

    # Отправляем сообщение с выбором типа работы
    await update.message.reply_text(
        "🔧 Выберите тип работы (все расчёты в м²):",
        reply_markup=keyboard
    )
    print("[input_address] Сообщение с клавиатурой отправлено")
    return TaskStates.SELECT_WORK_TYPE


async def select_work_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    wt_id = int(query.data.split(":")[2])
    nt = context.user_data["new_task"]
    nt["work_type_id"] = wt_id

    try:
        wt = await db.db_get_work_type_by_id(wt_id)
        nt["work_type_name"] = wt["name"] if wt else "работа"
    except Exception:
        nt["work_type_name"] = "работа"

    await query.edit_message_text(
        f"Выбрано: <b>{nt['work_type_name']}</b>\n\nВведите площадь (м²):",
        reply_markup=InlineKeyboardMarkup([cancel_button()]),
        parse_mode="HTML"
    )
    return TaskStates.INPUT_AREA


async def input_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        area = float(update.message.text.replace(",", ".").strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Введите число (площадь в м²):",
            reply_markup=InlineKeyboardMarkup([cancel_button()])
        )
        return TaskStates.INPUT_AREA

    nt = context.user_data["new_task"]
    nt["volume"] = area

    # 👇 РАСЧЁТ МАТЕРИАЛОВ ИЗ БД (через нормы)
    materials = await calc_service.calculate_materials_for_task(nt["work_type_id"], area)
    nt["calculated_materials"] = materials

    # 👇 ПРОВЕРКА: если это перегородки — задаём доп. вопросы
    work_type_name = nt.get("work_type_name", "").lower()
    if "перегород" in work_type_name:
        nt["is_partition"] = True
        await update.message.reply_text(
            "🛠️ Вы выбрали перегородки.\n"
            "Введите шаг профиля в миллиметрах (50, 75 или 100):",
            reply_markup=InlineKeyboardMarkup([cancel_button()])
        )
        return TaskStates.INPUT_PROFILE_STEP

    # Если не перегородки — сразу показываем расчёт и просим цены
    return await show_materials_and_ask_prices(update, context)


async def input_profile_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text not in ["50", "75", "100"]:
        await update.message.reply_text(
            "❌ Введите 50, 75 или 100:",
            reply_markup=InlineKeyboardMarkup([cancel_button()])
        )
        return TaskStates.INPUT_PROFILE_STEP

    nt = context.user_data["new_task"]
    nt["profile_step"] = int(text)

    await update.message.reply_text(
        "Выберите тип профиля:\n"
        "1 - CD (потолочный)\n"
        "2 - UW (направляющий)\n"
        "Введите номер (1 или 2):",
        reply_markup=InlineKeyboardMarkup([cancel_button()])
    )
    return TaskStates.INPUT_PROFILE_TYPE


async def input_profile_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text not in ["1", "2"]:
        await update.message.reply_text(
            "❌ Введите 1 или 2:",
            reply_markup=InlineKeyboardMarkup([cancel_button()])
        )
        return TaskStates.INPUT_PROFILE_TYPE

    nt = context.user_data["new_task"]
    nt["profile_type"] = "CD" if text == "1" else "UW"

    await update.message.reply_text(
        "Есть ли дверной проём?\n"
        "Введите 'да' или 'нет':",
        reply_markup=InlineKeyboardMarkup([cancel_button()])
    )
    return TaskStates.INPUT_DOOR


async def input_door(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    nt = context.user_data["new_task"]

    if text == "да":
        nt["has_door"] = True
        await update.message.reply_text(
            "Введите ширину двери в метрах (например, 0.9):",
            reply_markup=InlineKeyboardMarkup([cancel_button()])
        )
        return TaskStates.INPUT_DOOR_DIMENSIONS
    else:
        nt["has_door"] = False
        nt["door_width"] = 0
        nt["door_height"] = 0
        return await show_materials_and_ask_prices(update, context)


async def input_door_dimensions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        width = float(update.message.text.replace(",", ".").strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Введите число (ширину в метрах):",
            reply_markup=InlineKeyboardMarkup([cancel_button()])
        )
        return TaskStates.INPUT_DOOR_DIMENSIONS

    nt = context.user_data["new_task"]
    nt["door_width"] = width

    await update.message.reply_text(
        "Введите высоту двери в метрах (например, 2.1):",
        reply_markup=InlineKeyboardMarkup([cancel_button()])
    )
    return TaskStates.INPUT_DOOR_HEIGHT


async def input_door_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text.replace(",", ".").strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Введите число (высоту в метрах):",
            reply_markup=InlineKeyboardMarkup([cancel_button()])
        )
        return TaskStates.INPUT_DOOR_HEIGHT

    nt = context.user_data["new_task"]
    nt["door_height"] = height
    return await show_materials_and_ask_prices(update, context)


async def show_materials_and_ask_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список материалов и запрашивает цены"""
    nt = context.user_data["new_task"]
    area = nt["volume"]
    materials = nt.get("calculated_materials", [])

    if not materials:
        await update.message.reply_text(
            "❌ Не удалось рассчитать материалы.\n"
            "Проверьте, что для этого типа работ заданы нормы расхода.",
            reply_markup=InlineKeyboardMarkup([back_to_main_menu_button()])
        )
        return ConversationHandler.END

    text = f"📋 <b>Расчёт материалов для {nt['work_type_name']}</b>\n"
    text += f"📐 Площадь: {area} м²\n\n"
    text += "<b>По формуле рассчитаны:</b>\n"

    for i, m in enumerate(materials):
        text += f"{i+1}. {m['name']}: {m['qty']:.2f} {m['unit']} (базовая цена {m['price']} руб/{m['unit']})\n"

    # Если перегородки — добавляем параметры
    if nt.get("is_partition"):
        text += "\n📐 Параметры перегородки:\n"
        text += f"  • Шаг профиля: {nt.get('profile_step', '—')} мм\n"
        text += f"  • Тип профиля: {nt.get('profile_type', '—')}\n"
        text += f"  • Дверной проём: {'Да' if nt.get('has_door') else 'Нет'}\n"
        if nt.get('has_door'):
            text += f"  • Ширина двери: {nt.get('door_width', 0)} м\n"
            text += f"  • Высота двери: {nt.get('door_height', 0)} м\n"

    text += "\n<b>Введите цены материалов через запятую</b> (руб/ед.):\n"
    text += "Пример: 4500, 12, 2, 3, 45, 350\n"
    text += "Или отправьте «-» чтобы использовать базовые цены."

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([cancel_button()]),
        parse_mode="HTML"
    )
    return TaskStates.INPUT_MATERIAL_PRICES


async def input_material_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nt = context.user_data["new_task"]
    materials = nt.get("calculated_materials", [])
    text_input = update.message.text.strip()

    if text_input == "-":
        for m in materials:
            m["user_price"] = m["price"]
    else:
        try:
            prices = [float(p.strip()) for p in text_input.split(",")]
            if len(prices) != len(materials):
                await update.message.reply_text(
                    f"❌ Нужно {len(materials)} цен(ы), получено {len(prices)}. Попробуйте снова:",
                    reply_markup=InlineKeyboardMarkup([cancel_button()])
                )
                return TaskStates.INPUT_MATERIAL_PRICES
            for i, p in enumerate(prices):
                materials[i]["user_price"] = p
        except ValueError:
            await update.message.reply_text(
                "❌ Введите числа через запятую или «-»:",
                reply_markup=InlineKeyboardMarkup([cancel_button()])
            )
            return TaskStates.INPUT_MATERIAL_PRICES

    nt["materials"] = materials

    # Спрашиваем стоимость работы
    try:
        wt = await db.db_get_work_type_by_id(nt["work_type_id"])
        current_cost = wt["labor_cost_per_unit"] if wt else 0
    except Exception:
        current_cost = 0

    text = f"💰 <b>Стоимость работы</b>\n\n"
    if current_cost > 0:
        text += f"Текущая цена: {current_cost} руб/м²\n"
        text += f"Введите новую цену (руб/м²) или «-» чтобы оставить {current_cost}:"
    else:
        text += "Цена не задана. Введите стоимость работы за м² (руб):"

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([cancel_button()]),
        parse_mode="HTML"
    )
    return TaskStates.INPUT_LABOR_COST


async def input_labor_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nt = context.user_data["new_task"]
    text_input = update.message.text.strip()
    work_type_id = nt["work_type_id"]

    try:
        if text_input == "-":
            wt = await db.db_get_work_type_by_id(work_type_id)
            cost = wt["labor_cost_per_unit"] if wt and wt["labor_cost_per_unit"] else 0
        else:
            cost = float(text_input.replace(",", "."))
            await db.db_update_work_type_cost(work_type_id, cost)
    except ValueError:
        await update.message.reply_text(
            "❌ Введите число или «-»:",
            reply_markup=InlineKeyboardMarkup([cancel_button()])
        )
        return TaskStates.INPUT_LABOR_COST

    nt["labor_cost_override"] = cost
    return await show_calculation(update, context)


async def show_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nt = context.user_data["new_task"]
    area = nt["volume"]
    materials = nt.get("materials", [])
    labor_cost = nt.get("labor_cost_override", 0)

    total_labor = area * labor_cost
    total_mat_cost = 0.0

    text = f"📝 <b>Итоговый расчёт</b>\n\n"
    text += f"🏢 Сеть: {nt.get('network', '—')}\n"
    text += f"📍 Адрес: {nt.get('address', '—')}\n"
    text += f"🔧 Работа: {nt.get('work_type_name', '—')}\n"
    text += f"📐 Площадь: {area} м²\n"
    text += f"💰 Стоимость работы: {total_labor:,.2f} руб. ({labor_cost:,.2f} руб/м²)\n\n"
    text += "<b>Материалы (ваши цены):</b>\n"

    materials_payload = []
    for i, m in enumerate(materials):
        user_price = m.get("user_price", m["price"])
        cost = m["qty"] * user_price
        total_mat_cost += cost
        materials_payload.append({
            "material_id": m.get("material_id", i + 100),
            "calculated_qty": m["qty"],
            "final_qty": m["qty"],
        })
        text += f"• {m['name']}: {m['qty']:.2f} {m['unit']} × {user_price:.2f} = {cost:,.2f} руб.\n"

    # Если перегородки — показываем параметры в итоге
    if nt.get("is_partition"):
        text += "\n📐 Параметры перегородки:\n"
        text += f"  • Шаг профиля: {nt.get('profile_step', '—')} мм\n"
        text += f"  • Тип профиля: {nt.get('profile_type', '—')}\n"
        text += f"  • Дверной проём: {'Да' if nt.get('has_door') else 'Нет'}\n"

    text += f"\n<b>Итого материалы:</b> {total_mat_cost:,.2f} руб."
    text += f"\n<b>ИТОГО:</b> {total_labor + total_mat_cost:,.2f} руб."

    nt["materials_payload"] = materials_payload
    nt["total_materials"] = total_mat_cost
    nt["total_labor"] = total_labor

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Сохранить задачу", callback_data="task:save")],
        [InlineKeyboardButton("❌ Отмена", callback_data="dialog:cancel")]
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)

    return TaskStates.SHOW_CALCULATION


async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nt = context.user_data.pop("new_task", {})

    try:
        created = await db.db_create_task(
            object_id=nt["object_id"],
            work_type_id=nt["work_type_id"],
            volume=nt["volume"],
            labor_cost_override=nt.get("labor_cost_override"),
            materials=nt.get("materials_payload", []),
            profile_step=nt.get("profile_step"),
            profile_type=nt.get("profile_type"),
            has_door=nt.get("has_door", False),
            door_width=nt.get("door_width", 0),
            door_height=nt.get("door_height", 0)
        )
        await query.edit_message_text(f"✅ Задача #{created['id']} сохранена!")

        # 🔁 Синхронизация с Google Sheets
        from sheets.sync import sync_all
        try:
            await sync_all()
            logger.info("Google Sheets синхронизирован")
        except Exception as e:
            logger.error(f"Ошибка синхронизации Google Sheets: {e}")

    except Exception as e:
        await query.edit_message_text(f"⚠️ Ошибка сохранения: {e}")

    from bot.handlers.start import main_menu_callback
    await main_menu_callback(update, context)
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

    context.user_data.pop("new_task", None)
    context.user_data.pop("calculated_materials", None)
    return ConversationHandler.END


def get_handlers():
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_create_task, pattern="^menu:tasks:create$")],
        states={
            TaskStates.SELECT_NETWORK: [CallbackQueryHandler(select_network, pattern="^net:.*$")],
            TaskStates.INPUT_ADDRESS: [MessageHandler(filters.ALL, input_address)],
            TaskStates.SELECT_WORK_TYPE: [CallbackQueryHandler(select_work_type, pattern="^task:wt:\\d+$")],
            TaskStates.INPUT_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_area)],
            TaskStates.INPUT_PROFILE_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_profile_step)],
            TaskStates.INPUT_PROFILE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_profile_type)],
            TaskStates.INPUT_DOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_door)],
            TaskStates.INPUT_DOOR_DIMENSIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_door_dimensions)],
            TaskStates.INPUT_DOOR_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_door_height)],
            TaskStates.INPUT_MATERIAL_PRICES: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_material_prices)],
            TaskStates.INPUT_LABOR_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_labor_cost)],
            TaskStates.SHOW_CALCULATION: [
                CallbackQueryHandler(save_task, pattern="^task:save$"),
                CallbackQueryHandler(cancel_dialog, pattern="^dialog:cancel$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_dialog, pattern="^dialog:cancel$"),
            CommandHandler("cancel", cancel_dialog),
        ],
    )
    return [conv]