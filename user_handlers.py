"""
handlers/user_handlers.py
"""

from __future__ import annotations

import logging
import json
import pytz
from datetime import date, datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
)
from telegram.ext.filters import TEXT, COMMAND, StatusUpdate

import config
from client import get_db
from booking_service import BookingService
from formatters import format_today_list, format_booking_card, DIVIDER

logger = logging.getLogger(__name__)

(
    CONFIRM_BOOKING,
    SELECT_DATE,
    SELECT_START_TIME,
    SELECT_END_TIME,
    ENTER_TOPIC,
    SELECT_ROOM,
    QUICK_SELECT_ROOM,
) = range(7)

TIME_SLOTS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
    "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
    "17:00", "17:30", "18:00",
]


def _build_room_keyboard(prefix: str = "room"):
    keyboard = [
        [InlineKeyboardButton(f"🏢 {name}", callback_data=f"{prefix}:{room_id}")]
        for room_id, name in config.ROOMS.items()
    ]
    keyboard.append([InlineKeyboardButton("✖️ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)


def _build_date_keyboard():
    today = date.today()
    dates = []
    for i in range(14):
        d = today + timedelta(days=i)
        label = "Today" if i == 0 else ("Tomorrow" if i == 1 else d.strftime("%a, %b %d"))
        dates.append(InlineKeyboardButton(label, callback_data=f"date:{d.isoformat()}"))
    keyboard = []
    for i in range(0, len(dates), 2):
        row = [dates[i]]
        if i + 1 < len(dates):
            row.append(dates[i + 1])
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✖️ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)


def _build_time_keyboard(selected_date: str, prefix: str):
    keyboard = []
    row = []
    for i, slot in enumerate(TIME_SLOTS):
        row.append(InlineKeyboardButton(slot, callback_data=f"time_{prefix}:{selected_date}:{slot}"))
        if (i + 1) % 4 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back:date:{selected_date}")])
    keyboard.append([InlineKeyboardButton("✖️ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)


async def cmd_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📱 *Room Booking App*\n\nTap below to open the booking interface:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("⚡ Open Booking App", web_app=WebAppInfo(config.WEBAPP_URL))]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
        parse_mode="Markdown",
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_admin = user.id in config.ADMIN_IDS

    text = (
        f"👋 *Welcome, {user.first_name}!*\n"
        f"{DIVIDER}\n"
        f"Manage conference room bookings right here in Telegram.\n\n"
        f"*Commands*\n"
        f"📅 /today — Today's room schedule\n"
        f"📋 /mybookings — Your bookings & status\n"
        f"➕ /book — Book a conference room\n"
        f"🔓 /release — Release an active booking\n"
    )

    if is_admin:
        text += (
            f"\n*Admin*\n"
            f"📬 /pending — Review pending requests\n"
        )

    text += f"\n{DIVIDER}\n⚠️ _All bookings require admin approval._"
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Open Booking App", web_app=WebAppInfo(config.WEBAPP_URL))]],
            resize_keyboard=True,
        ),
        parse_mode="Markdown",
    )


async def cmd_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["booking"] = {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
    }
    await update.message.reply_text(
        f"➕ *New Booking*\n{DIVIDER}\n\n🏢 *Step 1 of 4* — Select a room:",
        reply_markup=_build_room_keyboard("room"),
        parse_mode="Markdown",
    )
    return SELECT_ROOM


async def room_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("✖️ Booking cancelled.")
        return ConversationHandler.END

    if query.data.startswith("room:"):
        room_id = query.data.split(":")[1]
        context.user_data["booking"]["room_id"] = room_id
        room_name = config.ROOMS.get(room_id, config.ROOM_NAME)
        await query.edit_message_text(
            f"➕ *New Booking*\n{DIVIDER}\n"
            f"🏢 *{room_name}*\n\n"
            f"📅 *Step 2 of 4* — Select a date:",
            reply_markup=_build_date_keyboard(),
            parse_mode="Markdown",
        )
        return SELECT_DATE

    return SELECT_ROOM


async def date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("✖️ Booking cancelled.")
        return ConversationHandler.END

    booking = context.user_data.get("booking", {})

    if query.data.startswith("date:"):
        selected_date = query.data.split(":", 1)[1]
        context.user_data["booking"]["booking_date"] = selected_date
        room_name = config.ROOMS.get(booking.get("room_id", "A"), config.ROOM_NAME)
        await query.edit_message_text(
            f"➕ *New Booking*\n{DIVIDER}\n"
            f"🏢 *{room_name}*\n"
            f"📅 *{selected_date}*\n\n"
            f"🕐 *Step 3 of 4* — Select start time:",
            reply_markup=_build_time_keyboard(selected_date, "start"),
            parse_mode="Markdown",
        )
        return SELECT_START_TIME

    if query.data.startswith("time_start:"):
        _, selected_date, selected_time = query.data.split(":", 2)
        context.user_data["booking"]["start_time"] = selected_time
        room_name = config.ROOMS.get(booking.get("room_id", "A"), config.ROOM_NAME)
        await query.edit_message_text(
            f"➕ *New Booking*\n{DIVIDER}\n"
            f"🏢 *{room_name}*\n"
            f"📅 *{selected_date}*  ·  🕐 *{selected_time}*\n\n"
            f"⏰ *Step 3 of 4* — Select end time:",
            reply_markup=_build_time_keyboard(selected_date, "end"),
            parse_mode="Markdown",
        )
        return SELECT_END_TIME

    if query.data.startswith("time_end:"):
        _, selected_date, selected_time = query.data.split(":", 2)
        context.user_data["booking"]["end_time"] = selected_time
        start = booking.get("start_time", "??:??")
        room_name = config.ROOMS.get(booking.get("room_id", "A"), config.ROOM_NAME)
        await query.edit_message_text(
            f"➕ *New Booking*\n{DIVIDER}\n"
            f"🏢 *{room_name}*\n"
            f"📅 *{selected_date}*  ·  🕐 *{start} – {selected_time}*\n\n"
            f"📝 *Step 4 of 4* — Enter the meeting topic:",
            parse_mode="Markdown",
        )
        return ENTER_TOPIC

    if query.data.startswith("back:date:"):
        await query.edit_message_text(
            f"➕ *New Booking*\n{DIVIDER}\n\n📅 *Step 2 of 4* — Select a date:",
            reply_markup=_build_date_keyboard(),
            parse_mode="Markdown",
        )
        return SELECT_DATE

    return SELECT_DATE


async def topic_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    topic = update.message.text.strip()
    booking = context.user_data["booking"]
    booking["topic"] = topic

    db = get_db()
    service = BookingService(db)
    result = service.request_booking(
        user_id=booking["user_id"],
        username=booking["username"],
        full_name=booking["full_name"],
        booking_date=booking["booking_date"],
        start_time=booking["start_time"],
        end_time=booking["end_time"],
        topic=booking["topic"],
        room_id=booking.get("room_id", "A"),
    )

    if not result.success:
        await update.message.reply_text(
            f"❌ *Booking Failed*\n{DIVIDER}\n{result.error}",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    b = result.booking
    st = b["start_time"][:5]
    et = b["end_time"][:5]

    room_name = config.ROOMS.get(booking.get("room_id", "A"), config.ROOM_NAME)
    await update.message.reply_text(
        f"✅ *Request Submitted!*\n"
        f"{DIVIDER}\n"
        f"🏢 *{room_name}*\n"
        f"📌 *{b['topic']}*\n"
        f"📅 *{b['booking_date']}*  ·  *{st} – {et}*\n"
        f"{DIVIDER}\n"
        f"🕐 Waiting for admin approval.\n"
        f"You'll be notified once reviewed.",
        parse_mode="Markdown",
    )

    await _notify_admins_new_request(context, b)
    logger.info("User %s submitted booking id=%s", booking["user_id"], b["id"])
    return ConversationHandler.END


async def cmd_quickbook(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["quickbook_user"] = {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
    }
    await update.message.reply_text(
        f"⚡ *Quick Book*\n{DIVIDER}\n\n🏢 Select a room to book instantly:",
        reply_markup=_build_room_keyboard("qroom"),
        parse_mode="Markdown",
    )
    return QUICK_SELECT_ROOM


async def quickbook_room_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("✖️ Cancelled.")
        return ConversationHandler.END

    if query.data.startswith("qroom:"):
        room_id = query.data.split(":")[1]
        user_data = context.user_data.get("quickbook_user", {})

        tz = pytz.timezone(config.TIMEZONE)
        now = datetime.now(tz)
        booking_date = now.strftime("%Y-%m-%d")
        start_time = now.strftime("%H:%M")
        end_time = "23:59"

        db = get_db()
        service = BookingService(db)

        result = service.request_booking(
            user_id=user_data["user_id"],
            username=user_data["username"],
            full_name=user_data["full_name"],
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            topic="Quick Book",
            room_id=room_id,
        )

        if not result.success:
            await query.edit_message_text(
                f"❌ *Quick Book Failed*\n{DIVIDER}\n{result.error}",
                parse_mode="Markdown",
            )
            return ConversationHandler.END

        admin_id = next(iter(config.ADMIN_IDS))
        approve_result = service.approve_booking(result.booking["id"], admin_id)
        if not approve_result.success:
            await query.edit_message_text(
                f"❌ *Could not confirm booking*\n{DIVIDER}\n{approve_result.error}",
                parse_mode="Markdown",
            )
            return ConversationHandler.END

        booking = approve_result.booking
        scheduler = context.bot_data.get("scheduler")
        if scheduler:
            scheduler.schedule_booking_jobs(booking)

        room_name = config.ROOMS.get(room_id, config.ROOM_NAME)
        await query.edit_message_text(
            f"⚡ *Quick Booked!*\n"
            f"{DIVIDER}\n"
            f"🏢 *{room_name}*\n"
            f"📅 *{booking_date}*  ·  *{start_time} – {end_time}*\n"
            f"{DIVIDER}\n"
            f"Room is yours. Use /release when done. 🔓",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    return QUICK_SELECT_ROOM


async def cmd_release(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = get_db()
    service = BookingService(db)
    bookings = service.get_user_bookings(user.id)
    active = [b for b in bookings if b["status"] == "approved"]

    if not active:
        await update.message.reply_text(
            f"🔓 *Release Booking*\n{DIVIDER}\n"
            "You have no active bookings to release.",
            parse_mode="Markdown",
        )
        return

    keyboard = []
    for b in active:
        st = b["start_time"][:5]
        et = b["end_time"][:5]
        room_name = config.ROOMS.get(b.get("room_id", "A"), config.ROOM_NAME)
        keyboard.append([InlineKeyboardButton(
            f"🏢 {room_name}  ·  {b['booking_date']}  {st}–{et}",
            callback_data=f"release:{b['id']}",
        )])
    keyboard.append([InlineKeyboardButton("✖️ Cancel", callback_data="cancel")])

    await update.message.reply_text(
        f"🔓 *Release a Booking*\n{DIVIDER}\nSelect which booking to release:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def release_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("✖️ Cancelled.")
        return

    if query.data.startswith("release:"):
        booking_id = query.data.split(":")[1]
        db = get_db()
        service = BookingService(db)
        success = service.release_booking(booking_id)

        if success:
            await query.edit_message_text(
                f"🔓 *Booking Released*\n{DIVIDER}\nThe room is now available.",
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text(
                "❌ Could not release booking. Please try again.",
                parse_mode="Markdown",
            )


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    today = date.today().isoformat()
    db = get_db()
    service = BookingService(db)
    bookings = service.get_today_bookings(today)
    await update.message.reply_text(format_today_list(bookings, today), parse_mode="Markdown")


async def cmd_mybookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = get_db()
    service = BookingService(db)
    bookings = service.get_user_bookings(user.id)

    if not bookings:
        await update.message.reply_text(
            f"📋 *My Bookings*\n{DIVIDER}\n"
            "_You have no bookings yet._\n\n"
            "Use /book to reserve a room. 📅",
            parse_mode="Markdown",
        )
        return

    lines = [f"📋 *My Bookings*\n{DIVIDER}\n"]
    for i, b in enumerate(bookings, 1):
        lines.append(f"*{i}.* {format_booking_card(b)}")
        lines.append("")
    await update.message.reply_text("\n".join(lines).rstrip(), parse_mode="Markdown")


async def _notify_admins_new_request(context: ContextTypes.DEFAULT_TYPE, booking: dict) -> None:
    st = booking["start_time"][:5]
    et = booking["end_time"][:5]
    username_part = f"@{booking['username']}" if booking.get("username") else "no username"

    text = (
        f"🔔 *New Booking Request*\n"
        f"{DIVIDER}\n"
        f"🏢 *{config.ROOMS.get(booking.get('room_id', 'A'), config.ROOM_NAME)}*\n"
        f"👤 *{booking['full_name']}*  ·  {username_part}\n"
        f"📌 *{booking['topic']}*\n"
        f"📅 *{booking['booking_date']}*  ·  *{st} – {et}*\n"
        f"{DIVIDER}"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{booking['id']}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject:{booking['id']}"),
    ]])

    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        except Exception as exc:
            logger.warning("Could not notify admin %s: %s", admin_id, exc)


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.web_app_data:
        return

    try:
        data = json.loads(update.message.web_app_data.data)
        user = update.effective_user
        action = data.get("action")
        room = data.get("room", "A")

        db = get_db()
        service = BookingService(db)

        if action == "quick_book":
            result = service.request_booking(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                booking_date=data.get("date"),
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
                topic=data.get("topic", "Quick Book"),
                room_id=room,
            )
            if result.success:
                admin_id = next(iter(config.ADMIN_IDS))
                approve_result = service.approve_booking(result.booking["id"], admin_id)
                room_name = config.ROOMS.get(room, config.ROOM_NAME)
                if approve_result.success:
                    scheduler = context.bot_data.get("scheduler")
                    if scheduler:
                        scheduler.schedule_booking_jobs(approve_result.booking)
                await update.message.reply_text(
                    f"⚡ *Quick Booked!*\n"
                    f"{DIVIDER}\n"
                    f"🏢 *{room_name}*\n"
                    f"📅 *{data.get('date')}*  ·  *{data.get('start_time')} – {data.get('end_time')}*\n"
                    f"{DIVIDER}\n"
                    f"Room is yours. Tap *Release Room* when done. 🔓",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    f"❌ *Quick Book Failed*\n{DIVIDER}\n{result.error}",
                    parse_mode="Markdown",
                )

        elif action == "schedule_book":
            result = service.request_booking(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                booking_date=data.get("date"),
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
                topic=data.get("topic"),
                room_id=room,
            )
            if result.success:
                await update.message.reply_text(
                    f"✅ *Request Submitted!*\n"
                    f"{DIVIDER}\n"
                    f"🏢 *{config.ROOMS.get(room, config.ROOM_NAME)}*\n"
                    f"📌 *{data.get('topic')}*\n"
                    f"📅 *{data.get('date')}*  ·  *{data.get('start_time')} – {data.get('end_time')}*\n"
                    f"{DIVIDER}\n"
                    f"🕐 Waiting for admin approval.\n"
                    f"You'll be notified once reviewed.",
                    parse_mode="Markdown",
                )
                await _notify_admins_new_request(context, result.booking)
            else:
                await update.message.reply_text(
                    f"❌ *Booking Failed*\n{DIVIDER}\n{result.error}",
                    parse_mode="Markdown",
                )

        elif action == "quick_release":
            booking_id = data.get("booking_id")
            released = False
            if booking_id:
                released = service.release_booking(booking_id)
            else:
                for b in service.get_user_bookings(user.id):
                    if b["booking_date"] == data.get("date") and b["status"] == "approved":
                        released = service.release_booking(b["id"])
                        break
            if released:
                await update.message.reply_text(
                    f"🔓 *Room Released*\n{DIVIDER}\nThe room is now available.",
                    parse_mode="Markdown",
                )

    except Exception as e:
        logger.error("Error handling webapp data: %s", e)


def register_user_handlers(app: Application) -> None:
    async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text("✖️ Booking cancelled.")
        context.user_data.clear()
        return ConversationHandler.END

    book_conv = ConversationHandler(
        entry_points=[CommandHandler("book", cmd_book_start)],
        states={
            SELECT_ROOM:       [CallbackQueryHandler(room_callback)],
            SELECT_DATE:       [CallbackQueryHandler(date_callback)],
            SELECT_START_TIME: [CallbackQueryHandler(date_callback)],
            SELECT_END_TIME:   [CallbackQueryHandler(date_callback)],
            ENTER_TOPIC:       [MessageHandler(TEXT & ~COMMAND, topic_received)],
        },
        fallbacks=[CallbackQueryHandler(cancel_conv, pattern="^cancel$"), CommandHandler("cancel", cancel_conv)],
        name="book_conversation",
    )

    quickbook_conv = ConversationHandler(
        entry_points=[CommandHandler("quickbook", cmd_quickbook)],
        states={
            QUICK_SELECT_ROOM: [CallbackQueryHandler(quickbook_room_callback, pattern="^qroom:|^cancel$")],
        },
        fallbacks=[CallbackQueryHandler(cancel_conv, pattern="^cancel$"), CommandHandler("cancel", cancel_conv)],
        name="quickbook_conversation",
    )

    app.add_handler(book_conv)
    app.add_handler(quickbook_conv)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("webapp", cmd_webapp))
    app.add_handler(CommandHandler("quick", cmd_webapp))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("mybookings", cmd_mybookings))
    app.add_handler(CommandHandler("release", cmd_release))
    app.add_handler(CallbackQueryHandler(release_callback, pattern="^release:"))

    app.add_handler(MessageHandler(StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    logger.info("User handlers registered.")
