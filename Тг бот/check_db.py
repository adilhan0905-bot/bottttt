from db.database import SessionLocal
from db.models import Task, WorkType, Norm, Material

session = SessionLocal()

# Проверяем типы работ
work_types = session.query(WorkType).all()
print(f"Типы работ: {len(work_types)}")
for wt in work_types:
    print(f"  {wt.id}: {wt.name}")

# Проверяем материалы
materials = session.query(Material).all()
print(f"\nМатериалы: {len(materials)}")
for m in materials:
    print(f"  {m.id}: {m.name} ({m.unit})")

# Проверяем нормы
norms = session.query(Norm).all()
print(f"\nНормы: {len(norms)}")
for n in norms:
    wt = session.query(WorkType).filter(WorkType.id == n.work_type_id).first()
    mat = session.query(Material).filter(Material.id == n.material_id).first()
    print(f"  {wt.name if wt else '?'} → {mat.name if mat else '?'}: {n.quantity_per_unit}")

# Проверяем задачи
tasks = session.query(Task).all()
print(f"\nЗадачи: {len(tasks)}")
for t in tasks:
    wt = session.query(WorkType).filter(WorkType.id == t.work_type_id).first()
    print(f"  Задача #{t.id}: {wt.name if wt else '?'}, объём {t.volume}")

session.close()