from db.database import SessionLocal
from db.models import WorkType
session = SessionLocal()
print(session.query(WorkType).count())
session.close()