# 🌍 ربات تلگرام WeatherBell

ربات تلگرامی برای دریافت نقشه‌های هواشناسی از WeatherBell با اکانت شخصی.

## امکانات

- نقشه‌های GFS و ECMWF
- پارامترها: بارش، دما، باد، فشار سطح دریا
- منطقه: خاورمیانه (قابل تغییر)
- ارسال یک نقشه یا همه نقشه‌ها به صورت دسته‌ای
- محدودسازی دسترسی به کاربران مشخص

## دستورات ربات

| دستور | توضیح |
|-------|-------|
| `/start` | شروع و راهنما |
| `/maps` | انتخاب نقشه با کیبورد |
| `/gfs` | همه نقشه‌های GFS |
| `/ecmwf` | همه نقشه‌های ECMWF |
| `/all` | همه نقشه‌ها (۸ تصویر) |

## راه‌اندازی روی Railway

### ۱. ساخت ربات تلگرام
به [@BotFather](https://t.me/BotFather) پیام بدید:
```
/newbot
```
توکن رو کپی کنید.

### ۲. پیدا کردن آی‌دی تلگرام
به [@userinfobot](https://t.me/userinfobot) پیام بدید، عدد `Id` رو کپی کنید.

### ۳. Push به GitHub
```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/weatherbell-bot.git
git push -u origin main
```

### ۴. دپلوی روی Railway
1. به [railway.app](https://railway.app) برید
2. **New Project → Deploy from GitHub repo**
3. ریپو رو انتخاب کنید
4. روی **Variables** کلیک کنید و این‌ها رو اضافه کنید:

| متغیر | مقدار |
|-------|-------|
| `BOT_TOKEN` | توکن از BotFather |
| `WB_USERNAME` | ایمیل WeatherBell شما |
| `WB_PASSWORD` | رمز WeatherBell شما |
| `ALLOWED_USERS` | آی‌دی عددی تلگرام شما |

5. Railway خودکار build و deploy می‌کنه

### ۵. تست
به ربات پیام بدید: `/start`

## تغییر منطقه جغرافیایی

در فایل `scraper.py` مقدار `domain` رو عوض کنید:

| مقدار | منطقه |
|-------|-------|
| `mideast` | خاورمیانه |
| `iran` | ایران (اگر موجود باشه) |
| `global` | جهانی |
| `conus` | آمریکا |
| `europe` | اروپا |

## اضافه کردن نقشه جدید

در `scraper.py` در دیکشنری `MAPS` اضافه کنید:
```python
"gfs_snow": ("❄️ GFS · برف", "gfs-ops-all", "snow-total", "mideast"),
```

## نکته مهم

- هر بار که نقشه می‌خواید Chrome باز می‌شه و لاگین می‌کنه — ممکنه ۱۵-۳۰ ثانیه طول بکشه
- Railway پلن رایگان محدودیت حافظه داره؛ اگر ربات کرش کرد پلن Hobby رو بگیرید
