import os
import logging
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from scraper import MAPS, scraper

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "")  # کاربرهای مجاز (آی‌دی با کاما جدا)


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS.strip():
        return True  # اگر تنظیم نشده، همه مجازن
    return str(user_id) in [u.strip() for u in ALLOWED_USERS.split(",")]


# ── /start ────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return

    text = (
        "🌍 *ربات نقشه‌های هواشناسی WeatherBell*\n\n"
        "از دکمه‌های زیر نقشه مورد نظر را انتخاب کنید:\n\n"
        "📌 دستورات:\n"
        "/maps — انتخاب نقشه\n"
        "/gfs — همه نقشه‌های GFS\n"
        "/ecmwf — همه نقشه‌های ECMWF\n"
        "/all — همه نقشه‌ها (۸ تصویر)\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /maps — کیبورد انتخاب نقشه ───────────────────────────────────
async def maps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    keyboard = []
    row = []
    for i, (key, (label, *_)) in enumerate(MAPS.items()):
        row.append(InlineKeyboardButton(label, callback_data=f"map:{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("📦 همه GFS", callback_data="batch:gfs"),
                     InlineKeyboardButton("📦 همه ECMWF", callback_data="batch:ecmwf")])
    keyboard.append([InlineKeyboardButton("🌐 همه نقشه‌ها", callback_data="batch:all")])

    await update.message.reply_text(
        "🗺 *نقشه مورد نظر را انتخاب کنید:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ── ارسال یک نقشه ─────────────────────────────────────────────────
async def send_single_map(update: Update, context: ContextTypes.DEFAULT_TYPE, map_key: str):
    query = update.callback_query
    label, model, parameter, domain = MAPS[map_key]

    msg = await query.message.reply_text(f"⏳ در حال دریافت {label} ...")

    try:
        scraper.start()
        img_bytes = scraper.capture_map(map_key)
        scraper.stop()

        if img_bytes:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=io.BytesIO(img_bytes),
                caption=f"🗺 *{label}*\n🕐 آخرین ران مدل",
                parse_mode="Markdown"
            )
            await msg.delete()
        else:
            await msg.edit_text("❌ خطا در دریافت نقشه. لطفاً دوباره تلاش کنید.")

    except Exception as e:
        logger.error(f"send_single_map error: {e}")
        await msg.edit_text(f"❌ خطا: {str(e)[:100]}")
        scraper.stop()


# ── ارسال دسته‌ای ─────────────────────────────────────────────────
async def send_batch_maps(update: Update, context: ContextTypes.DEFAULT_TYPE, batch: str):
    query = update.callback_query

    if batch == "gfs":
        keys = [k for k in MAPS if k.startswith("gfs")]
        title = "GFS"
    elif batch == "ecmwf":
        keys = [k for k in MAPS if k.startswith("ecmwf")]
        title = "ECMWF"
    else:
        keys = list(MAPS.keys())
        title = "همه مدل‌ها"

    msg = await query.message.reply_text(f"⏳ در حال دریافت {len(keys)} نقشه {title} ...")

    try:
        scraper.start()

        media_group = []
        for key in keys:
            label = MAPS[key][0]
            await msg.edit_text(f"⏳ دریافت {label} ...")
            img_bytes = scraper.capture_map(key)
            if img_bytes:
                media_group.append(
                    InputMediaPhoto(
                        media=io.BytesIO(img_bytes),
                        caption=f"🗺 {label}"
                    )
                )

        scraper.stop()

        if media_group:
            # تلگرام حداکثر ۱۰ تصویر در یه گروه می‌پذیره
            for i in range(0, len(media_group), 10):
                chunk = media_group[i:i+10]
                await context.bot.send_media_group(
                    chat_id=query.message.chat_id,
                    media=chunk
                )
            await msg.delete()
        else:
            await msg.edit_text("❌ هیچ نقشه‌ای دریافت نشد.")

    except Exception as e:
        logger.error(f"send_batch_maps error: {e}")
        await msg.edit_text(f"❌ خطا: {str(e)[:100]}")
        scraper.stop()


# ── Callback handler ──────────────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_allowed(query.from_user.id):
        await query.answer("⛔ دسترسی ندارید.", show_alert=True)
        return

    data = query.data

    if data.startswith("map:"):
        map_key = data.split(":", 1)[1]
        await send_single_map(update, context, map_key)

    elif data.startswith("batch:"):
        batch = data.split(":", 1)[1]
        await send_batch_maps(update, context, batch)


# ── /gfs /ecmwf /all shortcuts ───────────────────────────────────
async def gfs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    # Fake callback query را شبیه‌سازی می‌کنیم
    class FakeQuery:
        message = update.message
        from_user = update.effective_user
        async def answer(self): pass
    class FakeUpdate:
        callback_query = FakeQuery()
        effective_user = update.effective_user
    await send_batch_maps(FakeUpdate(), context, "gfs")


async def ecmwf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    class FakeQuery:
        message = update.message
        from_user = update.effective_user
        async def answer(self): pass
    class FakeUpdate:
        callback_query = FakeQuery()
        effective_user = update.effective_user
    await send_batch_maps(FakeUpdate(), context, "ecmwf")


async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    class FakeQuery:
        message = update.message
        from_user = update.effective_user
        async def answer(self): pass
    class FakeUpdate:
        callback_query = FakeQuery()
        effective_user = update.effective_user
    await send_batch_maps(FakeUpdate(), context, "all")


# ── main ──────────────────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("maps", maps_command))
    app.add_handler(CommandHandler("gfs", gfs_command))
    app.add_handler(CommandHandler("ecmwf", ecmwf_command))
    app.add_handler(CommandHandler("all", all_command))
    app.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("ربات شروع به کار کرد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
