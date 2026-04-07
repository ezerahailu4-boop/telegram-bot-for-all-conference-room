"""
utils/formatters.py — Modern message formatting for all bot messages.
"""

from __future__ import annotations
from typing import Any

import config

STATUS_EMOJI: dict[str, str] = {
    "pending":  "🕐",
    "approved": "✅",
    "rejected": "❌",
}

STATUS_LABEL: dict[str, str] = {
    "pending":  "Pending Approval",
    "approved": "Approved",
    "rejected": "Rejected",
}

DIVIDER = "─────────────────────"


def _room_name(booking: dict[str, Any]) -> str:
    return config.ROOMS.get(booking.get("room_id", "A"), config.ROOM_NAME)


def format_booking_card(booking: dict[str, Any]) -> str:
    st = booking["start_time"][:5]
    et = booking["end_time"][:5]
    status = booking["status"]
    emoji = STATUS_EMOJI.get(status, "❓")
    label = STATUS_LABEL.get(status, status.title())

    lines = [
        f"{emoji} {booking['topic']}",
        f"🏢 {_room_name(booking)}",
        f"📅 {booking['booking_date']}  ·  {st} – {et}",
        f"📌 Status: {label}",
    ]

    if status == "rejected" and booking.get("rejection_reason"):
        lines.append(f"💬 {booking['rejection_reason']}")

    return "\n".join(lines)


def format_booking_list(bookings: list[dict[str, Any]], title: str) -> str:
    if not bookings:
        return f"*{title}*\n\n_No bookings found._"

    parts = [f"*{title}*\n"]
    for i, b in enumerate(bookings, 1):
        parts.append(f"*{i}.* {format_booking_card(b)}")
        parts.append("")

    return "\n".join(parts).rstrip()


def format_today_list(bookings: list[dict[str, Any]], date_str: str) -> str:
    if not bookings:
        return (
            f"📅 Today's Schedule\n"
            f"{DIVIDER}\n"
            f"{date_str}\n\n"
            "✅ All rooms are free today!"
        )

    from collections import defaultdict
    by_room: dict[str, list] = defaultdict(list)
    for b in bookings:
        by_room[b.get("room_id", "A")].append(b)

    lines = [f"📅 Today's Schedule\n{DIVIDER}\n{date_str}\n"]
    for room_id, room_bookings in sorted(by_room.items()):
        lines.append(f"🏢 {config.ROOMS.get(room_id, config.ROOM_NAME)}")
        for b in sorted(room_bookings, key=lambda x: x["start_time"]):
            st = b["start_time"][:5]
            et = b["end_time"][:5]
            lines.append(f"  🕐 {st} – {et}  ·  {b['topic']}")
            lines.append(f"  👤 {b['full_name']}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_pending_card(booking: dict[str, Any]) -> str:
    st = booking["start_time"][:5]
    et = booking["end_time"][:5]
    username_part = f"@{booking['username']}" if booking.get("username") else "no username"
    return (
        f"🔔 New Booking Request\n"
        f"{DIVIDER}\n"
        f"🏢 {_room_name(booking)}\n"
        f"👤 {booking['full_name']}  ·  {username_part}\n"
        f"📌 {booking['topic']}\n"
        f"📅 {booking['booking_date']}  ·  {st} – {et}\n"
        f"{DIVIDER}"
    )


def format_approved_confirmation(booking: dict[str, Any]) -> str:
    st = booking["start_time"][:5]
    et = booking["end_time"][:5]
    return (
        f"🎉 Booking Approved!\n"
        f"{DIVIDER}\n"
        f"🏢 {_room_name(booking)}\n"
        f"📌 {booking['topic']}\n"
        f"📅 {booking['booking_date']}  ·  {st} – {et}\n"
        f"{DIVIDER}\n"
        f"⏰ You'll get a reminder {config.REMINDER_MINUTES_BEFORE} min before.\n"
        f"See you there! 👋"
    )


def format_rejected_confirmation(booking: dict[str, Any]) -> str:
    st = booking["start_time"][:5]
    et = booking["end_time"][:5]
    reason = booking.get("rejection_reason") or "No reason provided."
    return (
        f"❌ Booking Rejected\n"
        f"{DIVIDER}\n"
        f"🏢 {_room_name(booking)}\n"
        f"📌 {booking['topic']}\n"
        f"📅 {booking['booking_date']}  ·  {st} – {et}\n"
        f"{DIVIDER}\n"
        f"💬 Reason: {reason}\n\n"
        f"Try a different time with /book 📅"
    )
