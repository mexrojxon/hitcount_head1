import sys
import asyncio
import random
import re
from typing import Final

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import ClientSession, ClientTimeout, TCPConnector, web
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

# ---------------- AIOHTTP WEB SERVER ----------------
async def handle_home(request):
    return web.Response(text="Bot ishlayapti ✅")

async def start_web_server():
    web_app = web.Application()
    web_app.router.add_get("/", handle_home)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Web server started on port 8080")

# ---------------- MAIN ----------------
async def main():
    # Web server va botni birgalikda main loop da ishlatamiz
    await start_web_server()
    print("Bot polling started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
