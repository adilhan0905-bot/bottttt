from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🏗 Добавить объект", callback_data="menu:tasks:create")],
        [InlineKeyboardButton("💵 Указать стоимость материалов", callback_data="menu:set:material_prices")],
        [InlineKeyboardButton("🔨 Указать стоимость работы за каждый тип работы", callback_data="menu:set:labor_costs")],
        [InlineKeyboardButton("📊  Google таблица", callback_data="menu:sheets")],
    ]
    return InlineKeyboardMarkup(buttons)

def back_to_main_menu_button() -> list:
    return [InlineKeyboardButton("« Главное меню", callback_data="menu:main")]


def cancel_button() -> list:
    return [InlineKeyboardButton("❌ Отмена", callback_data="dialog:cancel")]


def confirm_cancel_row() -> list:
    return [
        InlineKeyboardButton("✅ Подтвердить", callback_data="dialog:confirm"),
        InlineKeyboardButton("❌ Отмена", callback_data="dialog:cancel"),
    ]


def network_select_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🟢 Магнит", callback_data="net:Магнит"),
         InlineKeyboardButton("🔴 Пятёрочка", callback_data="net:Пятёрочка")],
        [InlineKeyboardButton("❌ Отмена", callback_data="dialog:cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def objects_list_keyboard(objects: list[dict], action_prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for obj in objects:
        net = f"[{obj.get('network', '—')}] " if obj.get('network') else ""
        text = f"{net}{obj['name']} ({obj.get('address', 'без адреса')})"
        buttons.append([InlineKeyboardButton(text, callback_data=f"{action_prefix}:{obj['id']}")])
    buttons.append(back_to_main_menu_button())
    return InlineKeyboardMarkup(buttons)


def work_types_list_keyboard(work_types: list[dict], action_prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for wt in work_types:
        text = f"{wt['name']} ({wt['unit']}, {wt['labor_cost_per_unit']} руб/м²)"
        buttons.append([InlineKeyboardButton(text, callback_data=f"{action_prefix}:{wt['id']}")])
    buttons.append(back_to_main_menu_button())
    return InlineKeyboardMarkup(buttons)


def materials_list_keyboard(materials: list[dict], action_prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for m in materials:
        price_str = f"{m['default_price']} руб" if m.get('default_price') is not None else "цена не задана"
        text = f"{m['name']} ({m['unit']}, {price_str})"
        buttons.append([InlineKeyboardButton(text, callback_data=f"{action_prefix}:{m['id']}")])
    buttons.append(back_to_main_menu_button())
    return InlineKeyboardMarkup(buttons)


def tasks_list_keyboard(tasks: list[dict], action_prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for t in tasks:
        text = f"Задача #{t['id']} — {t.get('work_type_name', '???')} ({t['volume']} {t.get('unit', '')})"
        buttons.append([InlineKeyboardButton(text, callback_data=f"{action_prefix}:{t['id']}")])
    buttons.append(back_to_main_menu_button())
    return InlineKeyboardMarkup(buttons)


def task_materials_edit_keyboard(materials: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for m in materials:
        text = f"✏️ {m['name']}: {m['final_qty']} {m['unit']}"
        buttons.append([InlineKeyboardButton(text, callback_data=f"tm:edit:{m['id']}")])

    buttons.append([
        InlineKeyboardButton("💰 Изм. стоимость работы", callback_data="task:edit_labor"),
        InlineKeyboardButton("✅ Сохранить задачу", callback_data="task:save")
    ])
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="dialog:cancel")])
    return InlineKeyboardMarkup(buttons)


def purchase_status_keyboard(task_material_id: int, is_purchased: bool) -> InlineKeyboardMarkup:
    text = "✅ Уже закуплено" if not is_purchased else "❌ Отметить незакупленным"
    callback = f"purchase:toggle:{task_material_id}:{int(not is_purchased)}"
    buttons = [
        [InlineKeyboardButton(text, callback_data=callback)],
        [InlineKeyboardButton("💵 Указать факт. затраты", callback_data=f"purchase:cost:{task_material_id}")],
        [InlineKeyboardButton("« Назад", callback_data="menu:purchases")],
    ]
    return InlineKeyboardMarkup(buttons)


def yes_no_keyboard(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Да", callback_data=yes_callback),
         InlineKeyboardButton("Нет", callback_data=no_callback)]
    ])