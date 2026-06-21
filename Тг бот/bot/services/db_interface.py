import asyncio
import logging
from sqlalchemy import func
from db.database import SessionLocal
from db.models import WorkType, Material, Object, Task, TaskMaterial, Norm

logger = logging.getLogger(__name__)


# ======================= СИНХРОННАЯ ФУНКЦИЯ ДЛЯ ФИНАНСОВ (для тестов) =======================
def get_financial_summary(object_id: int = None) -> dict:
    session = SessionLocal()
    mat_cost_q = session.query(func.coalesce(func.sum(TaskMaterial.actual_cost), 0))
    labor_cost_q = session.query(func.coalesce(func.sum(Task.labor_cost_override), 0))
    if object_id:
        mat_cost_q = mat_cost_q.join(Task).filter(Task.object_id == object_id)
        labor_cost_q = labor_cost_q.filter(Task.object_id == object_id)
    total_materials = mat_cost_q.scalar() or 0.0
    total_labor = labor_cost_q.scalar() or 0.0
    session.close()
    return {
        'total_materials_cost': total_materials,
        'total_labor_cost': total_labor,
        'total': total_materials + total_labor
    }


# ======================= АСИНХРОННЫЕ ФУНКЦИИ ДЛЯ БОТА =======================

# --- Объекты ---
async def db_get_all_objects():
    def _get():
        session = SessionLocal()
        objs = session.query(Object).all()
        result = [{"id": o.id, "name": o.name, "network": o.network,
                   "address": o.address, "external_id": o.external_id} for o in objs]
        session.close()
        return result
    return await asyncio.to_thread(_get)

async def db_create_object(name: str, address: str = None, external_id: str = None, network: str = None):
    def _create():
        session = SessionLocal()
        obj = Object(name=name, address=address, external_id=external_id, network=network)
        session.add(obj)
        session.commit()
        obj_id = obj.id
        session.close()
        return {"id": obj_id, "name": name, "address": address, "network": network, "external_id": external_id}
    return await asyncio.to_thread(_create)

async def db_get_object_by_id(obj_id: int):
    def _get():
        session = SessionLocal()
        obj = session.query(Object).filter(Object.id == obj_id).first()
        if obj:
            result = {"id": obj.id, "name": obj.name, "address": obj.address,
                      "network": obj.network, "external_id": obj.external_id}
        else:
            result = None
        session.close()
        return result
    return await asyncio.to_thread(_get)

async def db_update_object(obj_id: int, name: str = None, address: str = None, external_id: str = None):
    def _update():
        session = SessionLocal()
        obj = session.query(Object).filter(Object.id == obj_id).first()
        if obj:
            if name is not None:
                obj.name = name
            if address is not None:
                obj.address = address
            if external_id is not None:
                obj.external_id = external_id
            session.commit()
        session.close()
    await asyncio.to_thread(_update)


# --- Типы работ ---
async def db_get_all_work_types():
    def _get():
        session = SessionLocal()
        wts = session.query(WorkType).all()
        result = [{"id": w.id, "name": w.name, "unit": w.unit,
                   "labor_cost_per_unit": w.labor_cost_per_unit} for w in wts]
        session.close()
        return result
    return await asyncio.to_thread(_get)

async def db_get_work_type_by_id(wt_id: int):
    def _get():
        session = SessionLocal()
        wt = session.query(WorkType).filter(WorkType.id == wt_id).first()
        result = None
        if wt:
            result = {"id": wt.id, "name": wt.name, "unit": wt.unit,
                      "labor_cost_per_unit": wt.labor_cost_per_unit}
        session.close()
        return result
    return await asyncio.to_thread(_get)

async def db_update_work_type_cost(wt_id: int, new_cost: float):
    def _up():
        session = SessionLocal()
        wt = session.query(WorkType).filter(WorkType.id == wt_id).first()
        if wt:
            wt.labor_cost_per_unit = new_cost
            session.commit()
            logger.info(f"Обновлена стоимость для WorkType ID {wt_id}: {new_cost}")
        else:
            logger.warning(f"WorkType с ID {wt_id} не найден.")
        session.close()
    await asyncio.to_thread(_up)


# --- Материалы ---
async def db_get_all_materials():
    def _get():
        session = SessionLocal()
        mats = session.query(Material).all()
        result = [{"id": m.id, "name": m.name, "unit": m.unit, "default_price": m.default_price} for m in mats]
        session.close()
        return result
    return await asyncio.to_thread(_get)

async def db_get_material_by_id(mat_id: int):
    def _get():
        session = SessionLocal()
        m = session.query(Material).filter(Material.id == mat_id).first()
        if m:
            result = {"id": m.id, "name": m.name, "unit": m.unit, "default_price": m.default_price}
        else:
            result = None
        session.close()
        return result
    return await asyncio.to_thread(_get)


# --- Нормы расхода ---
async def db_set_norm(work_type_id: int, material_id: int, quantity_per_unit: float):
    def _set():
        session = SessionLocal()
        norm = session.query(Norm).filter(
            Norm.work_type_id == work_type_id,
            Norm.material_id == material_id
        ).first()
        if norm:
            norm.quantity_per_unit = quantity_per_unit
        else:
            norm = Norm(
                work_type_id=work_type_id,
                material_id=material_id,
                quantity_per_unit=quantity_per_unit
            )
            session.add(norm)
        session.commit()
        session.close()
    await asyncio.to_thread(_set)

async def db_get_norms_with_materials(work_type_id: int):
    def _get():
        session = SessionLocal()
        norms = session.query(Norm).filter(Norm.work_type_id == work_type_id).all()
        result = []
        for n in norms:
            mat = session.query(Material).filter(Material.id == n.material_id).first()
            if mat:
                result.append({
                    "material_id": mat.id,
                    "material_name": mat.name,
                    "material_unit": mat.unit,
                    "quantity_per_unit": n.quantity_per_unit,
                    "default_price": mat.default_price
                })
        session.close()
        return result
    return await asyncio.to_thread(_get)


# --- Задачи ---
async def db_create_task(
        object_id: int,
        work_type_id: int,
        volume: float,
        labor_cost_override: float = None,
        materials: list = None,
        profile_step: int = None,
        profile_type: str = None,
        has_door: bool = False,
        door_width: float = 0.0,
        door_height: float = 0.0
):
    def _create():
        session = SessionLocal()
        task = Task(
            object_id=object_id,
            work_type_id=work_type_id,
            volume=volume,
            labor_cost_override=labor_cost_override,
            profile_step=profile_step,
            profile_type=profile_type,
            has_door=has_door,
            door_width=door_width,
            door_height=door_height
        )
        session.add(task)
        session.flush()
        if materials:
            for m in materials:
                tm = TaskMaterial(
                    task_id=task.id,
                    material_id=m.get("material_id", 0),
                    calculated_qty=m["calculated_qty"],
                    final_qty=m["final_qty"],
                    is_purchased=False,
                    actual_cost=None
                )
                session.add(tm)
        session.commit()
        task_id = task.id
        session.close()
        return {"id": task_id, "object_id": object_id, "work_type_id": work_type_id, "volume": volume}
    return await asyncio.to_thread(_create)

async def db_get_tasks_by_object(object_id: int = None):
    def _get():
        session = SessionLocal()
        q = session.query(Task)
        if object_id:
            q = q.filter(Task.object_id == object_id)
        tasks = q.all()
        result = []
        for t in tasks:
            wt = session.query(WorkType).filter(WorkType.id == t.work_type_id).first()
            result.append({
                "id": t.id,
                "object_id": t.object_id,
                "work_type_name": wt.name if wt else "???",
                "unit": wt.unit if wt else "",
                "volume": t.volume,
                "labor_cost_override": t.labor_cost_override,
                "all_purchased": t.all_purchased,
                "profile_step": t.profile_step,
                "profile_type": t.profile_type,
                "has_door": t.has_door,
                "door_width": t.door_width,
                "door_height": t.door_height
            })
        session.close()
        return result
    return await asyncio.to_thread(_get)

async def db_get_task_by_id(task_id: int):
    def _get():
        session = SessionLocal()
        t = session.query(Task).filter(Task.id == task_id).first()
        if not t:
            return None
        wt = session.query(WorkType).filter(WorkType.id == t.work_type_id).first()
        tm_list = session.query(TaskMaterial).filter(TaskMaterial.task_id == t.id).all()
        materials = []
        for tm in tm_list:
            mat = session.query(Material).filter(Material.id == tm.material_id).first()
            materials.append({
                "id": tm.id,
                "name": mat.name if mat else "???",
                "unit": mat.unit if mat else "",
                "final_qty": tm.final_qty,
                "is_purchased": tm.is_purchased,
                "actual_cost": tm.actual_cost
            })
        result = {
            "id": t.id,
            "object_id": t.object_id,
            "work_type_name": wt.name if wt else "???",
            "volume": t.volume,
            "labor_cost_override": t.labor_cost_override,
            "all_purchased": t.all_purchased,
            "materials": materials,
            "profile_step": t.profile_step,
            "profile_type": t.profile_type,
            "has_door": t.has_door,
            "door_width": t.door_width,
            "door_height": t.door_height
        }
        session.close()
        return result
    return await asyncio.to_thread(_get)


# --- Закупки ---
async def db_set_task_all_purchased(task_id: int, value: bool):
    def _up():
        session = SessionLocal()
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.all_purchased = value
            session.commit()
        session.close()
    await asyncio.to_thread(_up)

async def mark_material_purchased(tm_id: int, is_purchased: bool):
    def _up():
        session = SessionLocal()
        tm = session.query(TaskMaterial).filter(TaskMaterial.id == tm_id).first()
        if tm:
            tm.is_purchased = is_purchased
            session.commit()
        session.close()
    await asyncio.to_thread(_up)

async def set_actual_cost(tm_id: int, cost: float):
    def _up():
        session = SessionLocal()
        tm = session.query(TaskMaterial).filter(TaskMaterial.id == tm_id).first()
        if tm:
            tm.actual_cost = cost
            session.commit()
        session.close()
    await asyncio.to_thread(_up)

async def db_get_shopping_list():
    def _get():
        session = SessionLocal()
        items = session.query(TaskMaterial).filter(TaskMaterial.is_purchased == False).all()
        # Группировка по material_id
        groups = {}
        for tm in items:
            mat = session.query(Material).filter(Material.id == tm.material_id).first()
            if not mat:
                continue
            key = mat.id
            if key not in groups:
                groups[key] = {
                    "name": mat.name,
                    "unit": mat.unit,
                    "total_qty": 0.0,
                    "estimated_cost": 0.0
                }
            groups[key]["total_qty"] += tm.final_qty
            # estimated_cost можно взять из Task? или из material default? пока 0
        session.close()
        return list(groups.values())
    return await asyncio.to_thread(_get)


# --- Финансы (асинхронная обёртка) ---
async def db_get_finance_summary(object_id: int = None):
    def _get():
        return get_financial_summary(object_id)
    return await asyncio.to_thread(_get)


# --- Алиасы для обратной совместимости (если где-то используется create_task) ---
create_task = db_create_task