"""
services/scheduler_service.py — APScheduler wrapper for booking notifications.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from telegram import Bot

import config
from formatters import DIVIDER

logger = logging.getLogger(__name__)


class SchedulerService:

    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._tz = pytz.timezone(config.TIMEZONE)
        self._scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            timezone=self._tz,
        )

    def start(self) -> None:
        self._scheduler.start()
        logger.info("Scheduler started (timezone=%s).", config.TIMEZONE)

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down.")

    def schedule_booking_jobs(self, booking: dict[str, Any]) -> None:
        booking_id: str = booking["id"]
        user_id: int = int(booking["user_id"])
        topic: str = booking["topic"]
        date_str: str = booking["booking_date"]
        start_str: str = booking["start_time"][:5]
        end_str: str = booking["end_time"][:5]
        room_name: str = config.ROOMS.get(booking.get("room_id", "A"), config.ROOM_NAME)

        naive_start = datetime.fromisoformat(f"{date_str}T{start_str}")
        aware_start = self._tz.localize(naive_start)
        reminder_time = aware_start - timedelta(minutes=config.REMINDER_MINUTES_BEFORE)
        now = datetime.now(self._tz)

        reminder_id = f"reminder_{booking_id}"
        if reminder_time > now:
            self._scheduler.add_job(
                self._send_reminder,
                trigger="date",
                run_date=reminder_time,
                id=reminder_id,
                replace_existing=True,
                kwargs={
                    "user_id": user_id,
                    "topic": topic,
                    "start_time": start_str,
                    "end_time": end_str,
                    "date_str": date_str,
                    "room_name": room_name,
                },
            )
            logger.info("Scheduled reminder job %s at %s", reminder_id, reminder_time)

        start_id = f"start_{booking_id}"
        if aware_start > now:
            self._scheduler.add_job(
                self._send_start_notification,
                trigger="date",
                run_date=aware_start,
                id=start_id,
                replace_existing=True,
                kwargs={
                    "user_id": user_id,
                    "topic": topic,
                    "start_time": start_str,
                    "end_time": end_str,
                    "date_str": date_str,
                    "room_name": room_name,
                },
            )
            logger.info("Scheduled start job %s at %s", start_id, aware_start)

    def cancel_booking_jobs(self, booking_id: str) -> None:
        for prefix in ("reminder_", "start_"):
            job_id = f"{prefix}{booking_id}"
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
                logger.info("Removed job %s", job_id)

    def reload_all_from_db(self, approved_bookings: list[dict[str, Any]]) -> None:
        count = 0
        for booking in approved_bookings:
            self.schedule_booking_jobs(booking)
            count += 1
        logger.info("Reloaded scheduler jobs for %d approved bookings.", count)

    async def _send_reminder(
        self,
        user_id: int,
        topic: str,
        start_time: str,
        end_time: str,
        date_str: str,
        room_name: str = "",
    ) -> None:
        room_name = room_name or config.ROOM_NAME
        text = (
            f"⏰ *Reminder — {config.REMINDER_MINUTES_BEFORE} min to go!*\n"
            f"{DIVIDER}\n"
            f"🏢 *{room_name}*\n"
            f"📌 *{topic}*\n"
            f"📅 *{date_str}*  ·  *{start_time} – {end_time}*\n"
            f"{DIVIDER}\n"
            f"Please head to the room now. 🚶"
        )
        await self._safe_send(user_id, text)

    async def _send_start_notification(
        self,
        user_id: int,
        topic: str,
        start_time: str,
        end_time: str,
        date_str: str,
        room_name: str = "",
    ) -> None:
        room_name = room_name or config.ROOM_NAME
        text = (
            f"🚀 *Your meeting has started!*\n"
            f"{DIVIDER}\n"
            f"🏢 *{room_name}*\n"
            f"📌 *{topic}*\n"
            f"📅 *{date_str}*  ·  *{start_time} – {end_time}*\n"
            f"{DIVIDER}\n"
            f"The room is yours until *{end_time}*. Good luck! 👋"
        )
        await self._safe_send(user_id, text)

    async def _safe_send(self, user_id: int, text: str) -> None:
        try:
            await self._bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.error("Failed to send notification to user %s: %s", user_id, exc)
