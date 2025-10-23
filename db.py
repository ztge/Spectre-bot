import aiosqlite
import asyncio
import time

CREATE_TRACKED = '''
CREATE TABLE IF NOT EXISTS tracked (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    username TEXT NOT NULL COLLATE NOCASE,
    added_at INTEGER NOT NULL
);
'''

CREATE_SETTINGS = '''
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    notify_channel_id INTEGER
);
'''

CREATE_NOTIF = '''
CREATE TABLE IF NOT EXISTS notifications (
    username TEXT PRIMARY KEY COLLATE NOCASE,
    last_available_notified INTEGER,
    last_unavailable_notified INTEGER
);
'''

class DB:
    def __init__(self, path: str):
        self.path = path
        self._lock = asyncio.Lock()

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(CREATE_TRACKED)
            await db.execute(CREATE_SETTINGS)
            await db.execute(CREATE_NOTIF)
            await db.commit()

    async def add_tracked(self, guild_id: int, channel_id: int, username: str, ts: int):
        async with self._lock:
            async with aiosqlite.connect(self.path) as db:
                await db.execute(
                    "INSERT INTO tracked (guild_id, channel_id, username, added_at) VALUES (?,?,?,?)",
                    (guild_id, channel_id, username.lower(), ts)
                )
                await db.commit()

    async def remove_tracked(self, guild_id: int, username: str):
        async with self._lock:
            async with aiosqlite.connect(self.path) as db:
                await db.execute(
                    "DELETE FROM tracked WHERE guild_id = ? AND username = ?",
                    (guild_id, username.lower())
                )
                await db.commit()

    async def list_for_guild(self, guild_id: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT id, channel_id, username, added_at FROM tracked WHERE guild_id = ?", (guild_id,))
            rows = await cur.fetchall()
            return rows

    async def all_tracked(self):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT id, guild_id, channel_id, username, added_at FROM tracked")
            rows = await cur.fetchall()
            return rows

    async def set_notify_channel(self, guild_id: int, channel_id: int):
        async with self._lock:
            async with aiosqlite.connect(self.path) as db:
                await db.execute(
                    "INSERT INTO guild_settings (guild_id, notify_channel_id) VALUES (?,?) ON CONFLICT(guild_id) DO UPDATE SET notify_channel_id=excluded.notify_channel_id;",
                    (guild_id, channel_id)
                )
                await db.commit()

    async def get_notify_channel(self, guild_id: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT notify_channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def get_notification_timestamps(self, username: str):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT last_available_notified, last_unavailable_notified FROM notifications WHERE username = ?", (username.lower(),))
            row = await cur.fetchone()
            return (row[0], row[1]) if row else (None, None)

    async def update_notification_timestamp(self, username: str, kind: str, ts: int):
        field = 'last_available_notified' if kind == 'available' else 'last_unavailable_notified'
        async with self._lock:
            async with aiosqlite.connect(self.path) as db:
                await db.execute(
                    "INSERT INTO notifications (username, last_available_notified, last_unavailable_notified) VALUES (?,?,?) ON CONFLICT(username) DO UPDATE SET {} = excluded.{};".format(field, field),
                    (username.lower(), ts if field=='last_available_notified' else None, ts if field=='last_unavailable_notified' else None)
                )
                await db.commit()
