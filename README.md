# 🏢 Telegram Conference Room Booking Bot

A production-ready Telegram bot for managing a single conference room with admin approval flow, conflict detection, and automated reminders.

---

## 📁 Project Structure

```
telegram-booking-bot/
├── main.py                    # Entry point
├── config.py                  # Settings & env vars
├── requirements.txt
├── .env.example
├── schema.sql                 # Supabase table definitions
│
├── database/
│   ├── __init__.py
│   └── client.py              # Supabase client wrapper
│
├── services/
│   ├── __init__.py
│   ├── booking_service.py     # Core booking logic
│   └── scheduler_service.py   # APScheduler + reminders
│
├── handlers/
│   ├── __init__.py
│   ├── user_handlers.py       # /start, /book, /today, /mybookings
│   └── admin_handlers.py      # /pending, approve/reject callbacks
│
└── utils/
    ├── __init__.py
    ├── formatters.py          # Message formatting helpers
    └── validators.py          # Input validation
```

---

## 🗄️ Supabase Schema

Run `schema.sql` in your Supabase SQL Editor.

---

## ⚙️ Setup

### 1. Clone & install dependencies

```bash
git clone <your-repo>
cd telegram-booking-bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy your **Bot Token**

### 3. Get your Admin Telegram User ID

Message [@userinfobot](https://t.me/userinfobot) — it will reply with your numeric user ID.

### 4. Set up Supabase

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** → paste and run `schema.sql`
3. Go to **Settings → API** → copy:
   - Project URL
   - `anon` public key

### 5. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=123456789
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_anon_key_here
TIMEZONE=Asia/Jakarta
```

### 6. Run locally

```bash
python main.py
```

---

## 🚀 Deploy

### Railway

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add all environment variables in the Railway dashboard
4. Railway auto-detects Python and runs `main.py`

### Render

1. Push to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
4. Add environment variables in the Render dashboard

---

## 🤖 Bot Commands

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message & usage guide |
| `/book YYYY-MM-DD HH:MM HH:MM topic` | Request a room booking |
| `/today` | View all approved bookings for today |
| `/mybookings` | View your bookings and their status |

**Example:**
```
/book 2024-12-25 09:00 10:30 Q4 Planning Meeting
```

### Admin Commands

| Command | Description |
|---------|-------------|
| `/pending` | List all pending booking requests with Approve/Reject buttons |

---

## 🔔 Notifications

- **10 minutes before** booking: reminder sent to the user
- **At booking start time**: start notification sent to the user
- Jobs are reloaded from the database on every bot startup
