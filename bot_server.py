import sys
import asyncio
import random
import re
from typing import Final
from threading import Thread

from flask import Flask

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from aiogram.client.default import DefaultBotProperties

# Windows fix
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ---------------- CONFIG ----------------
API_TOKEN: Final = "8504710117:AAGuWhtkOJDmT6FufTHQuHrYpijEuA7P47M"

URL_RE = re.compile(
    r"(?i)\b((?:https?://|ftp://|www\d{0,3}[.])[^\s()<>]+)"
)

# ---------------- BOT ----------------
bot = Bot(
    API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ---------------- FLASK ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti ✅"

# ---------------- TRAFIK ----------------
async def hit_url(url: str, hits: int, chat_id: int):
    sem = asyncio.Semaphore(5)
    timeout = ClientTimeout(total=5)
    connector = TCPConnector(limit=0, ssl=False)

    async with ClientSession(
        timeout=timeout,
        connector=connector,
        headers={"User-Agent": "Mozilla/5.0"}
    ) as sess:

        async def single_request(i: int):
            async with sem:
                try:
                    async with sess.head(url, allow_redirects=True):
                        pass
                except:
                    pass

        tasks = [asyncio.create_task(single_request(i)) for i in range(hits)]
        await asyncio.gather(*tasks)

    await bot.send_message(chat_id, f"✅ <b>{hits}</b> ta so'rov yuborildi.")

# ---------------- HANDLERS ----------------
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        "Menga havola yuboring. 110–200 ta request yuboraman."
    )

@dp.message(F.text & ~F.via_bot)
async def handle_link(msg: Message):
    text = msg.text.strip()
    m = URL_RE.search(text)

    if not m:
        await msg.reply("URL topilmadi.")
        return

    url = m.group(0)
    if url.startswith("www."):
        url = "http://" + url

    hits = random.randint(110, 200)

    await msg.reply(f"🚀 {hits} ta request yuborilmoqda...")

    asyncio.create_task(hit_url(url, hits, msg.chat.id))

# ---------------- RUN BOT ----------------
async def start_bot():
    await dp.start_polling(bot)

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

# ---------------- MAIN ----------------
# Botni alohida threadda ishga tushuramiz (gunicorn ham, to'g'ridan-to'g'ri ham ishlaydi)
bot_thread = Thread(target=run_bot, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
