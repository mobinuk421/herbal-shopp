import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Railway دیتابیس را از طریق متغیر محیطی معرفی می‌کند
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/herbal_db")

# اصلاح پروتکل برای سازگاری با SQLAlchemy جدید در صورت نیاز
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()