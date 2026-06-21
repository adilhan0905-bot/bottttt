import logging
from sheets.client import SheetsClient
from bot.services import db_interface as db

logger = logging.getLogger(__name__)
sheets = SheetsClient()

def ensure_headers():
    try:
        ws = sheets.get_sheet("Объекты")
        if ws and not ws.get_all_values():
            ws.append_row(["ID", "Название", "Адрес", "Сеть", "Внешний ID"])
        ws = sheets.get_sheet("Типы работ")
        if ws and not ws.get_all_values():
            ws.append_row(["ID", "Название", "Единица", "Цена за м²"])
        ws = sheets.get_sheet("Задачи")
        if ws and not ws.get_all_values():
            ws.append_row(["ID", "Объект", "Тип работы", "Объём (м²)", "Стоимость работы", "Стоимость материалов", "Общая стоимость", "Статус"])
        logger.info("Заголовки листов созданы/проверены")
    except Exception as e:
        logger.error(f"Ошибка при создании заголовков: {e}")

def clear_sheets():
    """Очищает все данные на листах (кроме заголовков)"""
    try:
        for sheet_name in ["Объекты", "Типы работ", "Задачи"]:
            ws = sheets.get_sheet(sheet_name)
            if ws:
                all_data = ws.get_all_values()
                if len(all_data) > 1:
                    ws.delete_rows(2, len(all_data))
                    logger.info(f"Лист '{sheet_name}' очищен")
    except Exception as e:
        logger.error(f"Ошибка очистки листов: {e}")

async def sync_all():
    if not sheets.spreadsheet:
        logger.error("Google Sheets недоступен")
        return False

    try:
        # Очищаем перед записью
        clear_sheets()
        ensure_headers()

        objects = await db.db_get_all_objects()
        ws = sheets.get_sheet("Объекты")
        if ws:
            # Заголовки уже есть, добавляем данные
            for obj in objects:
                ws.append_row([obj['id'], obj['name'], obj.get('address',''), obj.get('network',''), obj.get('external_id','')])
            logger.info(f"Объекты синхронизированы: {len(objects)}")

        work_types = await db.db_get_all_work_types()
        ws = sheets.get_sheet("Типы работ")
        if ws:
            for wt in work_types:
                ws.append_row([wt['id'], wt['name'], wt['unit'], wt.get('labor_cost_per_unit',0)])
            logger.info(f"Типы работ синхронизированы: {len(work_types)}")

        tasks = await db.db_get_tasks_by_object()
        ws = sheets.get_sheet("Задачи")
        if ws:
            for t in tasks:
                obj_name = next((o['name'] for o in objects if o['id']==t['object_id']), '')
                labor = (t.get('labor_cost_override') or 0) * t['volume']
                total_materials = 0
                total = labor + total_materials
                status = "Закуплено" if t.get('all_purchased') else "Не закуплено"
                ws.append_row([t['id'], obj_name, t['work_type_name'], t['volume'], labor, total_materials, total, status])
            logger.info(f"Задачи синхронизированы: {len(tasks)}")
        return True
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        return False