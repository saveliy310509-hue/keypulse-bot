import asyncio
import os
import sys
import logging
import uvicorn
import aiohttp
from app import app
import bot

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("keypulse")

bot_task = None
keepalive_task = None

async def self_ping():
    """Фоновый Keep-Alive пинг, чтобы бесплатный сервер 24/7 не уходил в спящий режим."""
    port = int(os.environ.get("PORT", 8000))
    await asyncio.sleep(20)  # Пауза для инициализации сервера
    
    external_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("APP_URL")
    url = f"{external_url}/health" if external_url else f"http://127.0.0.1:{port}/health"
    
    logger.info(f"[KeepAlive] Модуль 24/7 активен. Целевой URL: {url}")
    while True:
        try:
            await asyncio.sleep(600)  # Каждые 10 минут
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as resp:
                    logger.info(f"[KeepAlive] Пинг {url} -> {resp.status}")
        except Exception as e:
            logger.debug(f"[KeepAlive] Ошибка пинга: {e}")

@app.on_event("startup")
async def on_startup():
    global bot_task, keepalive_task
    logger.info("=" * 60)
    logger.info("[+] Запуск единого ядра KeyPulse (FastAPI + Telegram Bot 24/7)")
    logger.info("=" * 60)
    bot_task = asyncio.create_task(bot.main())
    keepalive_task = asyncio.create_task(self_ping())

@app.on_event("shutdown")
async def on_shutdown():
    global bot_task, keepalive_task
    logger.info("[-] Завершение работы KeyPulse...")
    if bot_task:
        bot_task.cancel()
    if keepalive_task:
        keepalive_task.cancel()
    if bot.bot and bot.bot.session:
        await bot.bot.session.close()

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "KeyPulse License Server & Bot",
        "timestamp": bot.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    logger.info(f"[+] Сервер запускается на http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
