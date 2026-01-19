import json
import time
import logging
import asyncio
from datetime import datetime

from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

# ================== SOZLAMALAR ==================
BOT_TOKEN = "8034565159:AAGRJooSaa4fqQ9Hs6MDx15qQio8VVnZ2Cs"
ADMIN_ID = 1926076672
URL = "https://certiport.uz/uz/register"

bot = Bot(token=BOT_TOKEN)
scheduler = BlockingScheduler()
last_hour_report = None

# ================== LOG ==================
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ================== TELEGRAM ASYNC ==================
async def tg_send(text):
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        parse_mode="Markdown"
    )

def send(text):
    asyncio.run(tg_send(text))

# ================== JSON ==================
def load_known():
    try:
        with open("known_dates.json", "r") as f:
            return json.load(f)
    except:
        return {"Toshkent": [], "Samarqand": []}

def save_known(data):
    with open("known_dates.json", "w") as f:
        json.dump(data, f, indent=2)

# ================== SELENIUM ==================
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# ================== SHAHAR TEKSHIRISH ==================
def check_city(city):
    driver = get_driver()
    driver.get(URL)
    time.sleep(5)

    Select(driver.find_element(By.NAME, "exam")).select_by_visible_text(
        "IC3 Digital Literacy GS5"
    )
    Select(driver.find_element(By.NAME, "language")).select_by_visible_text(
        "English"
    )
    Select(driver.find_element(By.NAME, "module")).select_by_visible_text(
        "Living Online"
    )
    Select(driver.find_element(By.NAME, "location")).select_by_visible_text(
        city
    )

    time.sleep(4)

    yellow_days = driver.find_elements(
        By.CSS_SELECTOR,
        "button.bg-warning, button.available"
    )

    dates = [d.text.strip() for d in yellow_days if d.text.strip().isdigit()]

    driver.quit()
    logging.info(f"{city} tekshirildi | Topildi: {dates}")
    return dates

# ================== ASOSIY MONITOR ==================
def monitor():
    global last_hour_report
    known = load_known()
    now = datetime.now()

    hourly_status = []
    exam_found = False

    for city in ["Toshkent", "Samarqand"]:
        dates = check_city(city)
        new_dates = list(set(dates) - set(known[city]))

        if new_dates:
            exam_found = True
            msg = (
                f"🚨 *IMTIHON OCHILDI!*\n\n"
                f"🏙 Shahar: {city}\n"
                f"📅 Sanalar: {', '.join(sorted(new_dates))}"
            )
            send(msg)
            logging.warning(f"YANGI IMTIHON | {city} | {new_dates}")
            known[city].extend(new_dates)

        hourly_status.append(
            f"🏙 {city}: {'Bor' if dates else 'Yo‘q'} "
            f"{'(' + ', '.join(dates) + ')' if dates else ''}"
        )

    save_known(known)

    # ⏱ HAR SOATLIK HISOBOT
    if last_hour_report is None or now.hour != last_hour_report:
        report = (
            f"⏱ *SOATLIK HISOBOT*\n"
            f"🕒 Vaqt: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
            + "\n".join(hourly_status)
        )
        send(report)
        logging.info("Soatlik hisobot yuborildi")
        last_hour_report = now.hour

# ================== START XABAR ==================
def startup_message():
    send(
        "🤖 *Certiport monitoring bot ishga tushdi!*\n"
        "⏱ Tekshiruv: har 5 daqiqa\n"
        "📡 Holat: sayt tekshirilmoqda..."
    )
    logging.info("Bot ishga tushdi")

# ================== SCHEDULER ==================
scheduler.add_job(monitor, "interval", minutes=5)
scheduler.add_job(startup_message, "date", run_date=datetime.now())

print("🤖 Bot ishga tushdi")
scheduler.start()
