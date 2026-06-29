import os
from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn

from database import get_db
import models

app = FastAPI(title="Herbal Shop API")
templates = Jinja2Templates(directory="templates")

# دیتای اولیه فرضی برای تست در صورت خالی بودن دیتابیس
def seed_db(db: Session):
    if db.query(models.Product).count() == 0:
        sample_products = [
            models.Product(title="دمنوش گل‌گاوزبان ارگانیک", description="آرام‌بخش طبیعی، مفید برای کاهش استرس و تنظیم خواب.", price=85000, image_url="https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500", benefit="آرامش‌بخش و اعصاب"),
            models.Product(title="روغن بنفشه خالص", description="تهیه شده به روش سنتی، مناسب برای شفافیت پوست و تسکین سردرد.", price=120000, image_url="https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500", benefit="پوست و مو"),
            models.Product(title="چای سبز و نعناع فلفلی", description="ترکیب بی‌نظیر برای چربی‌سوزی، افزایش انرژی و بهبود گوارش.", price=65000, image_url="https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=500", benefit="گوارش و لاغری")
        ]
        db.add_all(sample_products)
        db.commit()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    seed_db(db) # برای اولین بار دیتای فرضی می‌ریزد
    products = db.query(models.Product).all()
    return templates.TemplateResponse("index.html", {"request": request, "products": products})

if __name__ == "__main__":
    # دریافت پورت پویا از Railway
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)