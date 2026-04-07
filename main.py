"""
main.py — Entry point for the Conference Room Booking Bot.
"""

import asyncio
import logging
import sys

from telegram import BotCommand
from telegram.ext import Application

import config
from client import get_db
from user_handlers import register_user_handlers
from admin_handlers import register_admin_handlers
from booking_service import BookingService
from scheduler_service import SchedulerService

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand("start",       "Welcome & usage guide"),
    BotCommand("book",        "Request a room booking"),
    BotCommand("today",       "View today's schedule"),
    BotCommand("mybookings",  "Your bookings & status"),
    BotCommand("release",     "Release an active booking"),
    BotCommand("quickbook",   "Book the room instantly"),
    BotCommand("webapp",      "Open the booking web app"),
    BotCommand("pending",     "Admin: review pending requests"),
]


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands(BOT_COMMANDS)
    logger.info("Bot command menu registered.")

    scheduler = SchedulerService(app.bot)
    scheduler.start()
    app.bot_data["scheduler"] = scheduler

    db = get_db()
    service = BookingService(db)
    try:
        upcoming = service.get_upcoming_approved()
    except Exception as exc:
        logger.error("Could not load upcoming bookings from DB: %s", exc)
        upcoming = []
    scheduler.reload_all_from_db(upcoming)

    logger.info("Bot is online and ready.")


async def post_shutdown(app: Application) -> None:
    scheduler: SchedulerService | None = app.bot_data.get("scheduler")
    if scheduler:
        scheduler.shutdown()
    logger.info("Bot shut down cleanly.")


def main() -> None:
    logger.info(
        "Starting booking bot (admins: %s, timezone: %s)",
        sorted(config.ADMIN_IDS),
        config.TIMEZONE,
    )

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    register_user_handlers(app)
    register_admin_handlers(app)

    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
