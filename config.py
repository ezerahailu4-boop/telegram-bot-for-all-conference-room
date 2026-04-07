"""
config.py — Centralised settings loaded from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Check your .env file."
        )
    return value


# ── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = _require("TELEGRAM_BOT_TOKEN")

# Comma-separated admin IDs → frozenset of ints
_raw_admin_ids = _require("ADMIN_IDS")
ADMIN_IDS: frozenset[int] = frozenset(
    int(uid.strip()) for uid in _raw_admin_ids.split(",") if uid.strip()
)

# ── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_KEY: str = _require("SUPABASE_KEY")

# ── App ───────────────────────────────────────────────────────────────────────
TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
ROOM_NAME: str = os.getenv("ROOM_NAME", "Conference Room A")

ROOMS: dict[str, str] = {
    "A": os.getenv("ROOM_NAME", "Conference Room A"),
    "B": os.getenv("ROOM_B_NAME", "Conference Room B"),
}

WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://telegram-bot-for-all-conference-roo.vercel.app")

# How many minutes before start time to send reminder
REMINDER_MINUTES_BEFORE: int = 10
