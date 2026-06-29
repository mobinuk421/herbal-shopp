import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="Herbal Shop Core")
templates = Jinja2Templates(directory="templates")

# دیتابیس در حافظه (In-Memory Database) برای پایداری و سرعت بدون خرابی
PRODUCTS = [
    {
        "title": "دمنوش گل‌گاوزبان ارگانیک",
        "description": "آرام‌بخش طبیعی، مفید برای کاهش استرس و تنظیم خواب کیفیت درجه یک کوهستانی.",
        "price": 85000,
        "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500",
        "benefit": "آرامش‌بخش"
    },
    {
        "title": "روغن بنفشه خالص",
        "description": "تهیه شده به روش سنتی، مناسب برای شفافیت پوست و تسکین سردردهای مزمن.",
        "price": 120000,
        "image_url": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500",
        "benefit": "پوست و مو"
    },
    {
        "title": "چای سبز و نعناع فلفلی",
        "description": "ترکیب بی‌نظیر برای چربی‌سوزی طبیعی، افزایش انرژی روزانه و بهبود سیستم گوارش.",
        "price": 65000,
        "image_url": "https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=500",
        "benefit": "گوارش و لاغری"
    }
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "products": PRODUCTS})

@app.post("/add-product")
async def add_product(
    title: str = Form(...),
    benefit: str = Form(...),
    price: float = Form(...),
    image_url: str = Form(...),
    description: str = Form(...)
):
    # دریافت اطلاعات آنلاین و افزودن آن به لیست محصولات اصلی بدون وقفه
    new_item = {
        "title": title,
        "benefit": benefit,
        "price": price,
        "image_url": image_url,
        "description": description
    }
    PRODUCTS.insert(0, new_item) # محصول جدید بالا قرار می‌گیرد
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
