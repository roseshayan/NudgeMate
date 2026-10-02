import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from nudgemate import __version__
from nudgemate.config import settings
from nudgemate.database.db import db
from nudgemate.handlers import commands, messages, callbacks
from nudgemate.services.scheduler_service import scheduler_service

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("nudgemate")


async def main():
    logger.info(f"Starting NudgeMate v{__version__}...")

    # Validate settings
    validation_errors = settings.validate()
    if validation_errors:
        for err in validation_errors:
            logger.error(f"Configuration error: {err}")
        logger.error("Please configure .env before starting the bot.")
        sys.exit(1)

    # Initialize Database
    logger.info("Initializing database...")
    await db.init_db()

    # Initialize Bot & Dispatcher
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Register Routers (order matters: commands -> callbacks -> general messages)
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(messages.router)

    # Start Scheduler
    scheduler_service.start(bot)

    # Notify Admin on Startup
    if settings.ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"🤖 **NudgeMate با موفقیت راه‌اندازی شد!** (نسخه {__version__})\nهمه سرویس‌ها فعال و آماده کار هستند. 🚀",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"Could not send startup message to admin: {e}")

    logger.info("Bot is running and polling for updates...")

    try:
        # Drop pending updates to avoid spamming old reminders on reboot
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down NudgeMate...")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
