-- ============================================================
-- Conference Room Booking Bot — Supabase Schema
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- BOOKINGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS bookings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Telegram user info
    user_id         BIGINT          NOT NULL,
    username        TEXT,
    full_name       TEXT            NOT NULL,
    
    -- Booking details
    room_id         TEXT            NOT NULL DEFAULT 'A'
                        CHECK (room_id IN ('A', 'B', 'C')),
    booking_date    DATE            NOT NULL,
    start_time      TIME            NOT NULL,
    end_time        TIME            NOT NULL,
    topic           TEXT            NOT NULL,
    
    -- Status: pending | approved | rejected | released
    status          TEXT            NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'approved', 'rejected', 'released')),
    
    -- Admin who acted on this booking
    reviewed_by     BIGINT,
    reviewed_at     TIMESTAMPTZ,
    rejection_reason TEXT,
    released_at     TIMESTAMPTZ,
    
    -- Timestamps
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER bookings_updated_at
    BEFORE UPDATE ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- INDEXES
-- ============================================================

-- Fast lookup by user
CREATE INDEX IF NOT EXISTS idx_bookings_user_id
    ON bookings (user_id);

-- Fast lookup by date + status + room (used for conflict checks & /today)
CREATE INDEX IF NOT EXISTS idx_bookings_date_status
    ON bookings (booking_date, status, room_id);

-- Fast lookup of pending bookings (admin /pending command)
CREATE INDEX IF NOT EXISTS idx_bookings_status
    ON bookings (status)
    WHERE status = 'pending';

-- ============================================================
-- OPTIONAL: Row Level Security (RLS)
-- For service-key or anon-key usage with Supabase
-- If you use the anon key, you MUST enable RLS + policies.
-- If you use the service_role key, RLS is bypassed.
-- ============================================================

-- Enable RLS on the table
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

-- Allow all operations using the service_role key (bypasses RLS automatically)
-- For anon key, create a permissive policy (only do this in trusted environments):
CREATE POLICY "Allow all for service role"
    ON bookings
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ============================================================
-- SAMPLE DATA (optional, for testing)
-- ============================================================
-- INSERT INTO bookings (user_id, username, full_name, booking_date, start_time, end_time, topic, status)
-- VALUES
--   (123456789, 'admin_user', 'Admin User', CURRENT_DATE, '09:00', '10:00', 'Morning Standup', 'approved'),
--   (987654321, 'john_doe',   'John Doe',   CURRENT_DATE, '14:00', '15:00', 'Client Demo',     'pending');
