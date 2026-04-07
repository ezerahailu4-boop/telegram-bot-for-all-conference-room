"""
services/booking_service.py — Core booking business logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import config
from client import SupabaseDB

logger = logging.getLogger(__name__)


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class BookingResult:
    success: bool
    booking: dict[str, Any] | None = None
    error: str | None = None
    conflicts: list[dict[str, Any]] | None = None


# ── Service ───────────────────────────────────────────────────────────────────

class BookingService:
    """Encapsulates all booking-related business rules."""

    def __init__(self, db: SupabaseDB) -> None:
        self._db = db

    # ── Create ────────────────────────────────────────────────────────────────

    def request_booking(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        booking_date: str,
        start_time: str,
        end_time: str,
        topic: str,
        room_id: str = "A",
    ) -> BookingResult:
        """
        Validate and create a booking request.
        Returns BookingResult with success=True and the new record,
        or success=False with a human-readable error.
        """
        if start_time >= end_time:
            return BookingResult(
                success=False,
                error="⏰ End time must be *after* start time.",
            )

        conflicts = self._db.get_conflicting_bookings(
            booking_date, start_time, end_time, room_id
        )
        if conflicts:
            return BookingResult(
                success=False,
                error=self._format_conflict_error(conflicts),
                conflicts=conflicts,
            )

        try:
            booking = self._db.create_booking(
                user_id=user_id,
                username=username,
                full_name=full_name,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                topic=topic,
                room_id=room_id,
            )
            logger.info(
                "Booking request created: id=%s user_id=%s date=%s %s-%s",
                booking["id"], user_id, booking_date, start_time, end_time,
            )
            return BookingResult(success=True, booking=booking)
        except Exception as exc:
            logger.exception("Failed to create booking: %s", exc)
            return BookingResult(
                success=False,
                error="❌ Database error. Please try again later.",
            )

    # ── Admin actions ─────────────────────────────────────────────────────────

    def approve_booking(
        self, booking_id: str, admin_id: int
    ) -> BookingResult:
        """Approve a pending booking. Re-checks conflicts on approval."""
        booking = self._db.get_booking_by_id(booking_id)
        if not booking:
            return BookingResult(success=False, error="Booking not found.")

        if booking["status"] != "pending":
            return BookingResult(
                success=False,
                error=f"Booking is already *{booking['status']}*.",
            )

        conflicts = self._db.get_conflicting_bookings(
            booking["booking_date"],
            booking["start_time"],
            booking["end_time"],
            booking.get("room_id", "A"),
        )
        # Exclude itself (shouldn't be approved yet, but defensive)
        conflicts = [c for c in conflicts if c["id"] != booking_id]
        if conflicts:
            return BookingResult(
                success=False,
                error=(
                    "⚠️ Cannot approve — this slot now conflicts with an "
                    "already-approved booking:\n"
                    + self._format_conflict_error(conflicts)
                ),
                conflicts=conflicts,
            )

        try:
            updated = self._db.approve_booking(booking_id, admin_id)
            logger.info(
                "Booking approved: id=%s by admin=%s", booking_id, admin_id
            )
            return BookingResult(success=True, booking=updated)
        except Exception as exc:
            logger.exception("Failed to approve booking: %s", exc)
            return BookingResult(
                success=False, error="❌ Database error approving booking."
            )

    def reject_booking(
        self, booking_id: str, admin_id: int, reason: str = ""
    ) -> BookingResult:
        """Reject a pending booking."""
        booking = self._db.get_booking_by_id(booking_id)
        if not booking:
            return BookingResult(success=False, error="Booking not found.")

        if booking["status"] != "pending":
            return BookingResult(
                success=False,
                error=f"Booking is already *{booking['status']}*.",
            )

        try:
            updated = self._db.reject_booking(booking_id, admin_id, reason)
            logger.info(
                "Booking rejected: id=%s by admin=%s", booking_id, admin_id
            )
            return BookingResult(success=True, booking=updated)
        except Exception as exc:
            logger.exception("Failed to reject booking: %s", exc)
            return BookingResult(
                success=False, error="❌ Database error rejecting booking."
            )

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_today_bookings(self, date: str, room_id: str | None = None) -> list[dict[str, Any]]:
        return self._db.get_approved_bookings_for_date(date, room_id)

    def get_user_bookings(self, user_id: int) -> list[dict[str, Any]]:
        return self._db.get_bookings_by_user(user_id)

    def get_pending_bookings(self) -> list[dict[str, Any]]:
        return self._db.get_pending_bookings()

    def get_upcoming_approved(self) -> list[dict[str, Any]]:
        return self._db.get_approved_upcoming_bookings()

    def release_booking(self, booking_id: str) -> bool:
        return self._db.release_booking(booking_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _format_conflict_error(conflicts: list[dict[str, Any]]) -> str:
        room_name = config.ROOMS.get(conflicts[0].get("room_id", "A"), config.ROOM_NAME) if conflicts else config.ROOM_NAME
        lines = [f"⛔ *{room_name}* is already booked during that time:\n"]
        for c in conflicts:
            lines.append(
                f"  · {c['start_time'][:5]} – {c['end_time'][:5]}  |  {c['topic']}  (by {c['full_name']})"
            )
        lines.append("\nPlease choose a different time slot.")
        return "\n".join(lines)
