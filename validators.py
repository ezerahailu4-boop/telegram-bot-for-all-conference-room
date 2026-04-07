"""
utils/validators.py — Input parsing and validation for bot commands.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ParsedBookingCommand:
    booking_date: str   # YYYY-MM-DD
    start_time: str     # HH:MM
    end_time: str       # HH:MM
    topic: str


@dataclass
class ParseError:
    message: str


# ── Parser ────────────────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def parse_book_command(
    args: list[str],
) -> ParsedBookingCommand | ParseError:
    """
    Parse arguments from the /book command.

    Expected format:
        /book YYYY-MM-DD HH:MM HH:MM topic words here

    Returns ParsedBookingCommand on success, ParseError on failure.
    """
    if len(args) < 4:
        return ParseError(
            "❌ *Invalid format.*\n\n"
            "Usage:\n"
            "`/book YYYY-MM-DD HH:MM HH:MM Your Topic Here`\n\n"
            "Example:\n"
            "`/book 2024-12-25 09:00 10:30 Q4 Planning Meeting`"
        )

    date_str, start_str, end_str = args[0], args[1], args[2]
    topic = " ".join(args[3:]).strip()

    # ── Validate date format ──────────────────────────────────────────────────
    if not _DATE_RE.match(date_str):
        return ParseError(
            "❌ *Invalid date format.*\n"
            "Use `YYYY-MM-DD` (e.g. `2024-12-25`)."
        )

    try:
        booking_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return ParseError(
            f"❌ *Invalid date:* `{date_str}`\n"
            "Please enter a real calendar date."
        )

    if booking_date < date.today():
        return ParseError(
            "❌ *Cannot book in the past.*\n"
            f"Today is `{date.today().isoformat()}`. Please choose a future date."
        )

    # ── Validate time formats ─────────────────────────────────────────────────
    for label, t in (("start", start_str), ("end", end_str)):
        if not _TIME_RE.match(t):
            return ParseError(
                f"❌ *Invalid {label} time format.*\n"
                "Use `HH:MM` in 24-hour format (e.g. `09:30`, `14:00`)."
            )
        try:
            datetime.fromisoformat(f"2000-01-01T{t}")
        except ValueError:
            return ParseError(
                f"❌ *Invalid {label} time:* `{t}`\n"
                "Please enter a valid 24-hour time."
            )

    # ── Validate topic ────────────────────────────────────────────────────────
    if not topic:
        return ParseError("❌ *Topic cannot be empty.* Please provide a meeting title.")

    if len(topic) > 200:
        return ParseError(
            f"❌ *Topic is too long* ({len(topic)} chars).\n"
            "Please keep it under 200 characters."
        )

    return ParsedBookingCommand(
        booking_date=date_str,
        start_time=start_str,
        end_time=end_str,
        topic=topic,
    )
