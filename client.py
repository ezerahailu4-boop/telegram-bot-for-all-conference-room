"""
database/client.py — Supabase client singleton with typed helper methods.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import pytz

from supabase import create_client, Client

import config

logger = logging.getLogger(__name__)

_lock = __import__("threading").Lock()
_client: Client | None = None


def get_db() -> "SupabaseDB":
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                logger.info("Supabase client initialised.")
    return SupabaseDB(_client)


class SupabaseDB:
    TABLE = "bookings"

    def __init__(self, client: Client) -> None:
        self._db = client

    def create_booking(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        booking_date: str,
        start_time: str,
        end_time: str,
        topic: str,
        room_id: str = "A",
    ) -> dict[str, Any]:
        payload = {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time,
            "topic": topic,
            "room_id": room_id,
            "status": "pending",
        }
        result = self._db.table(self.TABLE).insert(payload).execute()
        return result.data[0]

    def get_approved_bookings_for_date(self, date: str, room_id: str | None = None) -> list[dict[str, Any]]:
        q = (
            self._db.table(self.TABLE)
            .select("*")
            .eq("booking_date", date)
            .eq("status", "approved")
        )
        if room_id:
            q = q.eq("room_id", room_id)
        return q.order("room_id").order("start_time").execute().data

    def get_bookings_by_user(self, user_id: int) -> list[dict[str, Any]]:
        result = (
            self._db.table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("booking_date", desc=True)
            .order("start_time", desc=True)
            .execute()
        )
        return result.data

    def get_pending_bookings(self) -> list[dict[str, Any]]:
        result = (
            self._db.table(self.TABLE)
            .select("*")
            .eq("status", "pending")
            .order("created_at")
            .execute()
        )
        return result.data

    def get_booking_by_id(self, booking_id: str) -> dict[str, Any] | None:
        result = (
            self._db.table(self.TABLE)
            .select("*")
            .eq("id", booking_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def get_approved_upcoming_bookings(self) -> list[dict[str, Any]]:
        today = datetime.now(pytz.timezone(config.TIMEZONE)).date().isoformat()
        result = (
            self._db.table(self.TABLE)
            .select("*")
            .eq("status", "approved")
            .gte("booking_date", today)
            .order("booking_date")
            .order("start_time")
            .execute()
        )
        return result.data

    def release_booking(self, booking_id: str) -> bool:
        result = (
            self._db.table(self.TABLE)
            .update({
                "status": "released",
                "released_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", booking_id)
            .execute()
        )
        return bool(result.data)

    def approve_booking(self, booking_id: str, admin_id: int) -> dict[str, Any]:
        result = (
            self._db.table(self.TABLE)
            .update({
                "status": "approved",
                "reviewed_by": admin_id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", booking_id)
            .execute()
        )
        return result.data[0]

    def reject_booking(
        self, booking_id: str, admin_id: int, reason: str = ""
    ) -> dict[str, Any]:
        result = (
            self._db.table(self.TABLE)
            .update({
                "status": "rejected",
                "reviewed_by": admin_id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "rejection_reason": reason,
            })
            .eq("id", booking_id)
            .execute()
        )
        return result.data[0]

    def get_conflicting_bookings(
        self, booking_date: str, start_time: str, end_time: str, room_id: str = "A"
    ) -> list[dict[str, Any]]:
        result = (
            self._db.table(self.TABLE)
            .select("*")
            .eq("booking_date", booking_date)
            .eq("status", "approved")
            .eq("room_id", room_id)
            .lt("start_time", end_time)
            .gt("end_time", start_time)
            .execute()
        )
        return result.data
