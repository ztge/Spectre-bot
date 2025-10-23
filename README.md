Spectre — Autonomous Username Tracker (Final)
============================================

This package contains Spectre — an autonomous, safe Discord username tracker.
Features:
- /track, /list, /remove, /status, /notifychannel set/clear
- /users-available command with filters (Letters, Numbers, Characters), length 3-5, starts_with, ends_with
- Real availability checks via Discord API search (Bot token required)
- Automatic generation and tracking of patterns (3L, 4L, 3N, 4N, faces, realwords)
- Notifier runs continuously and sends Available / No longer available messages
- Notification cooldown (default 24 hours) to prevent spam
- Persistence via SQLite (spectre.db)

Quick start:
1. Edit config.json or set BOT_TOKEN env var.
2. Create virtualenv and install dependencies:
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\Activate on Windows
   pip install -r requirements.txt
3. Run:
   python bot.py

Security:
- Keep your bot token secret.
- Keep MAX_ATTEMPTS_PER_HOUR low (default 2) to avoid hitting username-change limits.

