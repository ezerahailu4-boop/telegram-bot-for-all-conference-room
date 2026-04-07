"""
handlers/admin_handlers.py
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Callable

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import config
from client import get_db
from booking_service import BookingService
from scheduler_service import SchedulerService
from formatters import (
    format_pending_card,
    format_approved_confirmation,
    format_rejected_confirmation,
    DIVIDER,
)

logger = logging.getLogger(__name__)


def admin_only(handler: Callable) -> Callable:
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is None or user.id not in config.ADMIN_IDS:
            if update.message:
                await update.message.reply_text("🚫 This command is for admins only.")
            elif update.callback_query:
                await update.callback_query.answer("🚫 Admins only.", show_alert=True)
            return
        return await handler(update, context)
    return wrapper


@admin_only
async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    db = get_db()
    service = BookingService(db)
    bookings = service.get_pending_bookings()

    if not bookings:
        await update.message.reply_text(
            f"📬 *Pending Requests*\n{DIVIDER}\n✅ No pending requests right now.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"📬 <b>Pending Requests</b>\n{DIVIDER}\n"
        f"<b>{len(bookings)}</b> request{'s' if len(bookings) > 1 else ''} awaiting review:",
        parse_mode="HTML",
    )

    for booking in bookings:
        st = booking["start_time"][:5]
        et = booking["end_time"][:5]
        username_part = f"@{booking['username']}" if booking.get("username") else "no username"
        from formatters import _room_name
        text = (
            f"🔔 <b>New Booking Request</b>\n"
            f"{DIVIDER}\n"
            f"🏢 <b>{_room_name(booking)}</b>\n"
            f"👤 <b>{booking['full_name']}</b>  ·  {username_part}\n"
            f"📌 <b>{booking['topic']}</b>\n"
            f"📅 <b>{booking['booking_date']}</b>  ·  <b>{st} – {et}</b>\n"
            f"{DIVIDER}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{booking['id']}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{booking['id']}"),
        ]])
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


@admin_only
async def callback_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    booking_id = query.data.split(":", 1)[1]
    admin = update.effective_user

    db = get_db()
    service = BookingService(db)
    result = service.approve_booking(booking_id, admin.id)

    if not result.success:
        await query.edit_message_text(
            f"⚠️ *Could not approve*\n{DIVIDER}\n{result.error}",
            parse_mode="Markdown",
        )
        return

    booking = result.booking
    if not booking:
        return
    st = booking["start_time"][:5]
    et = booking["end_time"][:5]
    room_name = config.ROOMS.get(booking.get("room_id", "A"), config.ROOM_NAME)

    await query.edit_message_text(
        f"✅ *Approved*\n"
        f"{DIVIDER}\n"
        f"🏢 *{room_name}*\n"
        f"📌 *{booking['topic']}*\n"
        f"📅 *{booking['booking_date']}*  ·  *{st} – {et}*\n"
        f"👤 {booking['full_name']}\n"
        f"{DIVIDER}\n"
        f"_Approved by {admin.full_name}_",
        parse_mode="Markdown",
    )

    try:
        await context.bot.send_message(
            chat_id=booking["user_id"],
            text=format_approved_confirmation(booking),
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.warning("Could not notify user %s of approval: %s", booking["user_id"], exc)

    scheduler: SchedulerService = context.bot_data.get("scheduler")
    if scheduler:
        scheduler.schedule_booking_jobs(booking)

    logger.info("Booking %s approved by admin %s", booking_id, admin.id)


@admin_only
async def callback_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    booking_id = query.data.split(":", 1)[1]
    admin = update.effective_user

    db = get_db()
    service = BookingService(db)
    result = service.reject_booking(booking_id, admin.id, reason="Rejected by admin.")

    if not result.success:
        await query.edit_message_text(
            f"⚠️ *Could not reject*\n{DIVIDER}\n{result.error}",
            parse_mode="Markdown",
        )
        return

    booking = result.booking
    if not booking:
        return
    st = booking["start_time"][:5]
    et = booking["end_time"][:5]
    room_name = config.ROOMS.get(booking.get("room_id", "A"), config.ROOM_NAME)

    await query.edit_message_text(
        f"❌ *Rejected*\n"
        f"{DIVIDER}\n"
        f"🏢 *{room_name}*\n"
        f"📌 *{booking['topic']}*\n"
        f"📅 *{booking['booking_date']}*  ·  *{st} – {et}*\n"
        f"👤 {booking['full_name']}\n"
        f"{DIVIDER}\n"
        f"_Rejected by {admin.full_name}_",
        parse_mode="Markdown",
    )

    try:
        await context.bot.send_message(
            chat_id=booking["user_id"],
            text=format_rejected_confirmation(booking),
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.warning("Could not notify user %s of rejection: %s", booking["user_id"], exc)

    scheduler: SchedulerService = context.bot_data.get("scheduler")
    if scheduler:
        scheduler.cancel_booking_jobs(booking_id)

    logger.info("Booking %s rejected by admin %s", booking_id, admin.id)


def register_admin_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CallbackQueryHandler(callback_approve, pattern=r"^approve:"))
    app.add_handler(CallbackQueryHandler(callback_reject, pattern=r"^reject:"))
    logger.info("Admin handlers registered.")
