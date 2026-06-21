from bot.services.db_interface import create_task

# Создадим задачу: объект с id=1 (пока нет, но для теста создадим вручную)
# Нам нужен объект в базе. Сейчас его нет, поэтому создадим тестовый объект отдельно
from db.database import SessionLocal
from db.models import Object

session = SessionLocal()
obj = Object(name='Тестовый объект', external_id='OBJ-001')
session.add(obj)
session.commit()
object_id = obj.id
session.close()

# Теперь создадим задачу
result = create_task(object_id=object_id, work_type_id=1, volume=10)
print('Задача создана:')
for key, value in result.items():
    if key != 'materials':
        print(f'{key}: {value}')
print('Материалы:')
for m in result['materials']:
    print(f"  {m['material_name']}: {m['quantity']} {m['unit']} — {m['cost']} руб.")