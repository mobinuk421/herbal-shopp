from sqlalchemy import Column, Integer, String, Text, Float
from database import Base, engine

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, PRIMARY KEY=True, index=True)
    title = Column(String(100), index=True)
    description = Column(Text)
    price = Column(Float)
    image_url = Column(String(255))
    benefit = Column(String(255))  # خواص درمانی محصول

# ساخت جدول‌ها در دیتابیس در صورت عدم وجود
Base.metadata.create_all(bind=engine)