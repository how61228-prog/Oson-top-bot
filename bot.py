import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, SUPER_ADMIN_IDS
from database import init_db
from middlewares import AuthAndSubMiddleware
from handlers import admin_router, user_router


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        stream=sys.stdout,
    )

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error(
            "❌ BOT_TOKEN kiritilmagan! Iltimos, .env fayliga BOT_TOKEN va ADMIN_IDS qiymatlarini kiriting."
        )
        return

    await init_db()
    logging.info("✅ SQLite ma'lumotlar bazasi tayyor!")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register middleware for ban check and mandatory channel subscription
    dp.message.middleware(AuthAndSubMiddleware())
    dp.callback_query.middleware(AuthAndSubMiddleware())

    # Include routers (admin_router first so admin commands/states take priority)
    dp.include_router(admin_router)
    dp.include_router(user_router)

    me = await bot.get_me()
    logging.info(f"🚀 Bot ishga tushdi: @{me.username} (ID: {me.id})")
    logging.info(f"👮‍♂️ Super Adminlar: {SUPER_ADMIN_IDS}")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot to'xtatildi.")
