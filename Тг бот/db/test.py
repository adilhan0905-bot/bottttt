import os
print("Working directory:", os.getcwd())
from bot.services.db_interface import calculate_materials
# ID=1 — кирпичная кладка, объём 10 м2
result = calculate_materials(1, 10)
for item in result:
    print(f"{item['material_name']}: {item['quantity']} {item['unit']} — {item['cost']} руб.")
