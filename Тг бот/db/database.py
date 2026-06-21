# db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'norms.db')

engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    init_db()
    print(f'База данных создана по пути: {DB_PATH}')