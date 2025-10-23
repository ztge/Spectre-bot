import asyncio
import time
import logging
from checker import check_username_availability
from db import DB
from config import BOT_TOKEN, CHECK_INTERVAL_SECONDS, NOTIFICATION_COOLDOWN_SECONDS
from notify_helpers import make_available_embed, make_unavailable_embed

logger = logging.getLogger('spectre_notifier')

async def start_notifier(bot, db: DB):
    await bot.wait_until_ready()
    logger.info('Notifier started.')
    while not bot.is_closed():
        rows = await db.all_tracked()
        if not rows:
            await asyncio.sleep(10)
            continue
        for _id, guild_id, channel_id, username, added_at in rows:
            try:
                available, err = await check_username_availability(username, BOT_TOKEN)
            except Exception as e:
                logger.exception('Checker error for %s: %s', username, e)
                available, err = False, str(e)
            notify_ch_id = await db.get_notify_channel(guild_id)
            ch = bot.get_channel(notify_ch_id) if notify_ch_id else bot.get_channel(channel_id)
            if not ch:
                continue
            now = int(time.time())
            last_avail, last_unavail = await db.get_notification_timestamps(username)
            # Available
            if available:
                if not last_avail or (now - last_avail) >= NOTIFICATION_COOLDOWN_SECONDS:
                    embed = make_available_embed(username, bot.get_guild(guild_id).name if bot.get_guild(guild_id) else None)
                    await ch.send(embed=embed)
                    await db.update_notification_timestamp(username, 'available', now)
                await db.remove_tracked(guild_id, username)
            else:
                if not last_unavail or (now - last_unavail) >= NOTIFICATION_COOLDOWN_SECONDS:
                    embed = make_unavailable_embed(username, bot.get_guild(guild_id).name if bot.get_guild(guild_id) else None)
                    await ch.send(embed=embed)
                    await db.update_notification_timestamp(username, 'unavailable', now)
            await asyncio.sleep(2)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
