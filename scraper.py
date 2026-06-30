import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io

logger = logging.getLogger(__name__)

WB_USERNAME = os.getenv("WB_USERNAME")
WB_PASSWORD = os.getenv("WB_PASSWORD")

# نقشه‌های موجود: (نام فارسی, model, parameter, domain)
MAPS = {
    # ── GFS ──────────────────────────────────────────────
    "gfs_precip":   ("🌧 GFS · بارش",          "gfs-ops-all", "sfcprecip-24hr", "mideast"),
    "gfs_temp":     ("🌡 GFS · دما ۲ متری",     "gfs-ops-all", "sfctemp",        "mideast"),
    "gfs_wind":     ("💨 GFS · باد سطح",        "gfs-ops-all", "sfcwind",        "mideast"),
    "gfs_mslp":     ("🌀 GFS · فشار سطح دریا",  "gfs-ops-all", "mslp",           "mideast"),
    # ── ECMWF ────────────────────────────────────────────
    "ecmwf_precip": ("🌧 ECMWF · بارش",         "ecmwf-ops-all","sfcprecip-24hr","mideast"),
    "ecmwf_temp":   ("🌡 ECMWF · دما ۲ متری",  "ecmwf-ops-all","sfctemp",       "mideast"),
    "ecmwf_wind":   ("💨 ECMWF · باد سطح",      "ecmwf-ops-all","sfcwind",       "mideast"),
    "ecmwf_mslp":   ("🌀 ECMWF · فشار سطح دریا","ecmwf-ops-all","mslp",          "mideast"),
}


def build_map_url(model: str, parameter: str, domain: str) -> str:
    return f"https://maps.weatherbell.com/view/model/{model}?d={domain}&p={parameter}"


def get_chrome_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    try:
        # Railway محیط: chromedriver از PATH
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        # local: webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    return driver


class WeatherBellScraper:
    def __init__(self):
        self.driver = None
        self.logged_in = False

    def start(self):
        self.driver = get_chrome_driver()
        self.logged_in = False

    def stop(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.logged_in = False

    def login(self) -> bool:
        try:
            logger.info("در حال لاگین به WeatherBell...")
            self.driver.get("https://www.weatherbell.com/login")
            wait = WebDriverWait(self.driver, 20)

            user_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            user_field.clear()
            user_field.send_keys(WB_USERNAME)

            pass_field = self.driver.find_element(By.NAME, "password")
            pass_field.clear()
            pass_field.send_keys(WB_PASSWORD)

            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_btn.click()

            time.sleep(4)

            if "login" not in self.driver.current_url.lower():
                self.logged_in = True
                logger.info("لاگین موفق!")
                return True
            else:
                logger.error("لاگین ناموفق — URL هنوز login هست")
                return False

        except Exception as e:
            logger.error(f"خطا در لاگین: {e}")
            return False

    def capture_map(self, map_key: str) -> bytes | None:
        if map_key not in MAPS:
            return None

        label, model, parameter, domain = MAPS[map_key]

        try:
            if not self.logged_in:
                if not self.login():
                    return None

            url = build_map_url(model, parameter, domain)
            logger.info(f"در حال بارگذاری: {url}")
            self.driver.get(url)

            wait = WebDriverWait(self.driver, 30)

            # صبر برای لود شدن نقشه
            map_img = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.map-image, #map-image, .map-img, canvas"))
            )
            time.sleep(3)  # صبر برای رندر کامل

            # اسکرین‌شات از المان نقشه
            png_bytes = map_img.screenshot_as_png

            # بهینه‌سازی با PIL
            img = Image.open(io.BytesIO(png_bytes))
            img = img.convert("RGB")
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.error(f"خطا در گرفتن نقشه {map_key}: {e}")
            # اگر session منقضی شده، دوباره لاگین
            if "login" in self.driver.current_url.lower():
                self.logged_in = False
            return None

    def capture_all(self) -> dict:
        """همه نقشه‌ها رو می‌گیره و dict برمی‌گردونه"""
        results = {}
        for key in MAPS:
            img_bytes = self.capture_map(key)
            if img_bytes:
                results[key] = img_bytes
            time.sleep(2)
        return results


# Singleton برای استفاده در ربات
scraper = WeatherBellScraper()
