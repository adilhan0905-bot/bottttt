# sheets/client.py
import gspread
from google.oauth2.service_account import Credentials
import os
from bot.config import Config

SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

class SheetsClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        creds_file = os.path.join(current_dir, 'credentials.json')
        if not os.path.exists(creds_file):
            print("⚠️ credentials.json не найден. Google Sheets не будет работать.")
            self.spreadsheet = None
            return
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        self.gc = gspread.authorize(creds)
        try:
            self.spreadsheet = self.gc.open_by_key(Config.SPREADSHEET_ID)
            print(f"✅ Подключено к таблице: {self.spreadsheet.title}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.spreadsheet = None

    def get_sheet(self, name):
        if self.spreadsheet:
            try:
                return self.spreadsheet.worksheet(name)
            except:
                return self.spreadsheet.add_worksheet(title=name, rows=100, cols=20)
        return None