from db.database import SessionLocal
from db.models import WorkType, Norm, Material

session = SessionLocal()
wt = session.query(WorkType).filter(WorkType.name.like('%плитк%')).first()
if wt:
    norms = session.query(Norm).filter(Norm.work_type_id == wt.id).all()
    print(f"Найдено {len(norms)} норм для {wt.name}")
    for n in norms:
        mat = session.query(Material).filter(Material.id == n.material_id).first()
        print(f"  {mat.name}: {n.quantity_per_unit} {mat.unit}")
else:
    print("Тип работы 'Плитка' не найден")
session.close()