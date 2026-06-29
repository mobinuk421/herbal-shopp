import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="Herbal Shop")
templates = Jinja2Templates(directory="templates")

PRODUCTS = [
    {
        "title": "دمنوش گل‌گاوزبان ارگانیک",
        "description": "آرام‌بخش طبیعی، مفید برای کاهش استرس و تنظیم خواب کیفیت درجه یک.",
        "price": 85000,
        "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500",
        "benefit": "آرامش‌بخش"
    },
    {
        "title": "روغن بنفشه خالص",
        "description": "تهیه شده به روش سنتی، مناسب برای شفافیت پوست و تسکین سردرد.",
        "price": 120000,
        "image_url": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500",
        "benefit": "پوست و مو"
    },
    {
        "title": "چای سبز و نعناع فلفلی",
        "description": "ترکیب بی‌نظیر برای چربی‌سوزی، افزایش انرژی و بهبود سیستم گوارش.",
        "price": 65000,
        "image_url": "https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=500",
        "benefit": "گوارش و لاغری"
    }
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "products": PRODUCTS})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
