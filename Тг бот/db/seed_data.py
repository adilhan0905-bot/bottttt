import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, WorkType, Material, Norm

DB_PATH = os.path.join(BASE_DIR, 'norms.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def fill_test_data():
    print("Инициализация БД...")
    init_db()
    session = SessionLocal()

    # ---- 1. ТИПЫ РАБОТ ----
    work_types = [
        ('📐 Расчет площади фундамента', 'м²', 0),
        ('🪟 Расчет для оконных проемов', 'м²', 0),
        ('🧱 Расчет для перегородок', 'м²', 0),
        ('🏷 Площадь: плитки', 'м²', 0),
        ('🛠 Площадь: стяжки', 'м²', 0),
        ('🏠 Площадь потолка', 'м²', 0),
    ]
    wt_objects = []
    for name, unit, cost in work_types:
        wt = session.query(WorkType).filter_by(name=name).first()
        if not wt:
            wt = WorkType(name=name, unit=unit, labor_cost_per_unit=cost)
            session.add(wt)
            session.flush()
        wt_objects.append(wt)
    session.commit()
    print(f"✅ Добавлено {len(wt_objects)} типов работ")

    # ---- 2. МАТЕРИАЛЫ ----
    materials_data = [
        ("Бетон М200", "м³", 4500),
        ("Цемент М500", "кг", 12),
        ("Песок", "кг", 2),
        ("Щебень", "кг", 3),
        ("Арматура 12 мм", "кг", 45),
        ("Опалубка", "м²", 350),
        ("Штукатурка откосов", "кг", 15),
        ("Гипсокартон", "м²", 180),
        ("Подоконник", "шт", 1200),
        ("Герметик силиконовый", "кг", 350),
        ("Профиль металлический", "м", 85),
        ("Минеральная вата", "м³", 1200),
        ("Саморезы", "шт", 2),
        ("Керамическая плитка", "м²", 800),
        ("Плиточный клей", "кг", 25),
        ("Затирка", "кг", 350),
        ("Грунтовка", "л", 120),
        ("Крестики", "шт", 1),
        ("Фиброволокно", "кг", 180),
        ("Маяки", "м", 45),
        ("Краска потолочная", "л", 350),
        ("Шпаклёвка", "кг", 120),
        ("Малярный скотч", "м", 15),
    ]
    mat_objects = {}
    for name, unit, price in materials_data:
        mat = session.query(Material).filter_by(name=name).first()
        if not mat:
            mat = Material(name=name, unit=unit, default_price=price)
            session.add(mat)
            session.flush()
        mat_objects[name] = mat
    session.commit()
    print(f"✅ Добавлено {len(mat_objects)} материалов")

    # ---- 3. НОРМЫ РАСХОДА ----
    norms_data = {
        "📐 Расчет площади фундамента": [
            ("Бетон М200", 0.2),
            ("Цемент М500", 50),
            ("Песок", 150),
            ("Щебень", 250),
            ("Арматура 12 мм", 16),
            ("Опалубка", 0.5),
        ],
        "🪟 Расчет для оконных проемов": [
            ("Штукатурка откосов", 8),
            ("Гипсокартон", 1.5),
            ("Подоконник", 1),
            ("Герметик силиконовый", 0.3),
        ],
        "🧱 Расчет для перегородок": [
            ("Гипсокартон", 2),
            ("Профиль металлический", 5),
            ("Штукатурка откосов", 16),
            ("Минеральная вата", 0.05),
            ("Саморезы", 50),
        ],
        "🏷 Площадь: плитки": [
            ("Керамическая плитка", 1.1),
            ("Плиточный клей", 5),
            ("Затирка", 0.5),
            ("Грунтовка", 0.3),
            ("Крестики", 30),
        ],
        "🛠 Площадь: стяжки": [
            ("Цемент М500", 12.5),
            ("Песок", 50),
            ("Фиброволокно", 0.045),
            ("Маяки", 2),
        ],
        "🏠 Площадь потолка": [
            ("Краска потолочная", 0.3),
            ("Шпаклёвка", 1),
            ("Грунтовка", 0.2),
            ("Малярный скотч", 2),
        ],
    }

    for wt_name, materials in norms_data.items():
        wt = session.query(WorkType).filter_by(name=wt_name).first()
        if not wt:
            continue
        for mat_name, qty in materials:
            mat = session.query(Material).filter_by(name=mat_name).first()
            if not mat:
                continue
            norm = session.query(Norm).filter_by(work_type_id=wt.id, material_id=mat.id).first()
            if not norm:
                norm = Norm(work_type_id=wt.id, material_id=mat.id, quantity_per_unit=qty)
                session.add(norm)
            else:
                norm.quantity_per_unit = qty
    session.commit()
    print("✅ Нормы расхода добавлены")

    print("База данных успешно заполнена.")
    session.close()

if __name__ == '__main__':
    fill_test_data()