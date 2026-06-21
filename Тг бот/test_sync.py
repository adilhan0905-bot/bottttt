import asyncio
from sheets.sync import sync_all

async def test():
    print("🔄 Запуск синхронизации...")
    result = await sync_all()
    print(f"Результат: {result}")

if __name__ == "__main__":
    asyncio.run(test())