import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from PIL import Image
import io

logger = logging.getLogger(__name__)

WB_USERNAME = os.getenv("WB_USERNAME")
WB_PASSWORD = os.getenv("WB_PASSWORD")

MAPS = {
    "gfs_precip":   ("🌧 GFS · بارش",           "gfs-ops-all",  "sfcprecip-24hr", "mideast"),
    "gfs_temp":     ("🌡 GFS · دما ۲ متری",      "gfs-ops-all",  "sfctemp",        "mideast"),
    "gfs_wind":     ("💨 GFS · باد سطح",         "gfs-ops-all",  "sfcwind",        "mideast"),
    "gfs_mslp":     ("🌀 GFS · فشار سطح دریا",   "gfs-ops-all",  "mslp",           "mideast"),
    "ecmwf_precip": ("🌧 ECMWF · بارش",          "ecmwf-ops-all","sfcprecip-24hr", "mideast"),
    "ecmwf_temp":   ("🌡 ECMWF · دما ۲ متری",   "ecmwf-ops-all","sfctemp",        "mideast"),
    "ecmwf_wind":   ("💨 ECMWF · باد سطح",       "ecmwf-ops-all","sfcwind",        "mideast"),
    "ecmwf_mslp":   ("🌀 ECMWF · فشار سطح دریا", "ecmwf-ops-all","mslp",           "mideast"),
}


def build_map_url(model, parameter, domain):
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
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        from webdriver_manager.chrome import ChromeDriverManager
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

    def login(self):
        try:
            logger.info("در حال لاگین به WeatherBell...")
            self.driver.get("https://www.weatherbell.com/login")
            time.sleep(3)
            logger.info(f"URL: {self.driver.current_url} | Title: {self.driver.title}")

            wait = WebDriverWait(self.driver, 25)

            # پیدا کردن فیلد username با selector های مختلف
            user_field = None
            for by, sel in [
                (By.NAME, "username"),
                (By.NAME, "email"),
                (By.ID, "username"),
                (By.ID, "email"),
                (By.ID, "user_login"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[type='text']"),
            ]:
                try:
                    el = wait.until(EC.element_to_be_clickable((by, sel)))
                    user_field = el
                    logger.info(f"username field: {by}={sel}")
                    break
                except:
                    continue

            if not user_field:
                logger.error("فیلد username پیدا نشد!")
                logger.info(f"PAGE HTML:\n{self.driver.page_source[:3000]}")
                return False

            user_field.clear()
            user_field.send_keys(WB_USERNAME)

            # فیلد password
            pass_field = None
            for by, sel in [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.ID, "user_pass"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ]:
                try:
                    el = self.driver.find_element(by, sel)
                    if el.is_displayed():
                        pass_field = el
                        logger.info(f"password field: {by}={sel}")
                        break
                except:
                    continue

            if not pass_field:
                logger.error("فیلد password پیدا نشد!")
                return False

            pass_field.clear()
            pass_field.send_keys(WB_PASSWORD)

            # دکمه submit
            for by, sel in [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.ID, "wp-submit"),
                (By.CSS_SELECTOR, ".login-submit input"),
                (By.XPATH, "//button[contains(text(),'Log') or contains(text(),'Sign')]"),
            ]:
                try:
                    btn = self.driver.find_element(by, sel)
                    if btn.is_displayed():
                        btn.click()
                        logger.info(f"submit button: {by}={sel}")
                        break
                except:
                    continue

            time.sleep(5)
            logger.info(f"URL بعد از لاگین: {self.driver.current_url}")

            if "login" not in self.driver.current_url.lower():
                self.logged_in = True
                logger.info("✅ لاگین موفق!")
                return True
            else:
                logger.error("❌ لاگین ناموفق")
                logger.info(f"PAGE AFTER LOGIN:\n{self.driver.page_source[:2000]}")
                return False

        except Exception as e:
            logger.error(f"خطا در لاگین: {e}")
            return False

    def capture_map(self, map_key):
        if map_key not in MAPS:
            return None
        label, model, parameter, domain = MAPS[map_key]
        try:
            if not self.logged_in:
                if not self.login():
                    return None

            url = build_map_url(model, parameter, domain)
            logger.info(f"بارگذاری: {url}")
            self.driver.get(url)

            wait = WebDriverWait(self.driver, 30)
            map_img = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "img.map-image, #map-image, .map-img, canvas")
                )
            )
            time.sleep(3)

            png_bytes = map_img.screenshot_as_png
            img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.error(f"خطا در گرفتن نقشه {map_key}: {e}")
            if self.driver and "login" in self.driver.current_url.lower():
                self.logged_in = False
            return None

    def capture_all(self):
        results = {}
        for key in MAPS:
            img_bytes = self.capture_map(key)
            if img_bytes:
                results[key] = img_bytes
            time.sleep(2)
        return results


scraper = WeatherBellScraper()
