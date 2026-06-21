import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env из папки, где находится main.py (корень проекта)
BASE_DIR = Path(__file__).parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "")

    @staticmethod
    def validate():
        if not Config.BOT_TOKEN:
            raise ValueError(
                "❌ BOT_TOKEN не найден в .env файле!\n"
                "Проверьте, что файл .env лежит в корне проекта и содержит строку BOT_TOKEN=ваш_токен"
            )
        print("✅ BOT_TOKEN загружен успешно.")