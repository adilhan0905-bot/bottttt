from db.database import SessionLocal
from db.models import TaskMaterial, Task, Norm, Object, WorkType, Material

session = SessionLocal()

try:
    # Удаляем в порядке, обратном созданию (сначала дочерние)
    print("Удаление TaskMaterial...")
    session.query(TaskMaterial).delete()

    print("Удаление Task...")
    session.query(Task).delete()

    print("Удаление Object...")
    session.query(Object).delete()

    # Если хочешь очистить и справочники (типы работ, материалы, нормы) — раскомментируй:
    # print("Удаление Norm...")
    # session.query(Norm).delete()
    # print("Удаление WorkType...")
    # session.query(WorkType).delete()
    # print("Удаление Material...")
    # session.query(Material).delete()

    session.commit()
    print("✅ База данных очищена (объекты, задачи и их материалы удалены).")
except Exception as e:
    session.rollback()
    print(f"❌ Ошибка: {e}")
finally:
    session.close()