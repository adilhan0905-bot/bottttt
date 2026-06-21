# bot/services/calc_service.py
import logging
from typing import List, Dict, Any
from bot.services import db_interface as db

logger = logging.getLogger(__name__)

async def calculate_materials_for_task(work_type_id: int, volume: float) -> List[Dict[str, Any]]:
    """
    Асинхронно рассчитывает необходимые материалы на основе БД.
    """
    # Получаем все нормы для данного типа работ (через JOIN с таблицей Materials)
    norms = await db.db_get_norms_with_materials(work_type_id)
    if not norms:
        logger.warning(f"Для типа работ ID {work_type_id} не найдено норм расхода.")
        return []

    calculated_materials = []
    for norm in norms:
        # Получаем текущую цену на материал. Если её нет в БД, ставим 0.
        price = norm.get('default_price', 0)
        if price is None:
            price = 0

        material_data = {
            "name": norm['material_name'],
            "unit": norm['material_unit'],
            "qty": norm['quantity_per_unit'] * volume,
            "price": price,
            "material_id": norm['material_id']
        }
        calculated_materials.append(material_data)
    return calculated_materials