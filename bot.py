import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import os
import json
import time
import random

from db import DB
from generator import generate_sample_patterns, generate_filtered
from checker import check_username_availability
from notify_helpers import make_available_embed, make_unavailable_embed
import notify

# Load config
CFG = {}
if os.path.exists('config.json'):
    with open('config.json','r',encoding='utf-8') as f:
        CFG = json.load(f)

BOT_TOKEN = os.getenv('BOT_TOKEN') or CFG.get('BOT_TOKEN')
MAX_ATTEMPTS = int(CFG.get('MAX_ATTEMPTS_PER_HOUR', 2))
CHECK_INTERVAL = int(CFG.get('CHECK_INTERVAL_SECONDS', 300))
DB_PATH = CFG.get('DB_PATH','spectre.db')
NOTIF_COOLDOWN = int(CFG.get('NOTIFICATION_COOLDOWN_SECONDS', 86400))

if not BOT_TOKEN:
    print('Set BOT_TOKEN in env or config.json')
    raise SystemExit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('spectre')

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

db = DB(DB_PATH)

# background auto-generation: periodically add sample patterns to tracking
async def auto_generate_task():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            patterns = generate_sample_patterns(limit_per_group=100)
            # pick a few to add to tracking
            to_add = random.sample(patterns, min(30, len(patterns)))
            for p in to_add:
                # add to all guilds default channel: will be tracked with guild id and first text channel id as fallback
                for g in client.guilds:
                    ch = None
                    for c in g.text_channels:
                        if c.permissions_for(g.me).send_messages:
                            ch = c
                            break
                    if ch:
                        await db.add_tracked(g.id, ch.id, p, int(time.time()))
            await asyncio.sleep(3600)  # run every hour
        except Exception as e:
            logger.exception('Auto-generate error: %s', e)
            await asyncio.sleep(60)

@tree.command(name='track', description='Start tracking a username')
@app_commands.describe(username='username to track (e.g., love, x_x)')
async def cmd_track(interaction: discord.Interaction, username: str):
    await interaction.response.defer(thinking=True)
    username = username.strip()
    if len(username) < 2 or len(username) > 32:
        await interaction.followup.send('Invalid username length (2-32).')
        return
    await db.init()
    await db.add_tracked(interaction.guild_id, interaction.channel_id, username, int(time.time()))
    embed = make_available_embed(username, interaction.guild.name if interaction.guild else None)
    await interaction.followup.send(embed=embed)

@tree.command(name='list', description='List tracked usernames for this server')
async def cmd_list(interaction: discord.Interaction):
    await interaction.response.defer()
    await db.init()
    rows = await db.list_for_guild(interaction.guild_id)
    if not rows:
        await interaction.followup.send('No usernames tracked in this server.')
        return
    msg = '**Tracked usernames:**\n'
    for _id, channel_id, username, added_at in rows:
        ch = client.get_channel(channel_id)
        ch_name = ch.mention if ch else f'channel_id:{channel_id}'
        msg += f'- `{username}` (channel: {ch_name})\n'
    await interaction.followup.send(msg)

@tree.command(name='remove', description='Stop tracking a username')
@app_commands.describe(username='username to stop tracking')
async def cmd_remove(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    await db.init()
    await db.remove_tracked(interaction.guild_id, username)
    embed = make_unavailable_embed(username, interaction.guild.name if interaction.guild else None)
    await interaction.followup.send(embed=embed)

@tree.command(name='status', description='Show bot status and rate-limit info')
async def cmd_status(interaction: discord.Interaction):
    await interaction.response.defer()
    await db.init()
    msg = f'Bot: `{client.user}`\nRate limit: {MAX_ATTEMPTS} attempts/hour\nCheck interval: {CHECK_INTERVAL}s'
    await interaction.followup.send(msg)

@tree.command(name='notifychannel', description='Manage notification channel for this server')
@app_commands.describe(action='set or clear', channel='channel to send notifications to (when action=set)')
async def cmd_notifychannel(interaction: discord.Interaction, action: str, channel: discord.TextChannel = None):
    await interaction.response.defer()
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.followup.send('You need Manage Server permission to configure the notify channel.')
        return
    action = action.lower()
    await db.init()
    if action == 'set':
        if channel is None:
            await interaction.followup.send('Provide a channel when using action "set".')
            return
        await db.set_notify_channel(interaction.guild_id, channel.id)
        await interaction.followup.send(f'Notification channel set to {channel.mention}')
    elif action == 'clear':
        await db.set_notify_channel(interaction.guild_id, None)
        await interaction.followup.send('Notification channel cleared.')
    else:
        await interaction.followup.send("Invalid action. Use 'set' or 'clear'.")

# users-available command
@tree.command(name='users-available', description='Find real available usernames by filters.')
@app_commands.describe(
    filter='Letters, Numbers, or Characters',
    length='Length of usernames (3-5)',
    starts_with='Optional: must start with this character (A-Z, 0-9, _, .)',
    ends_with='Optional: must end with this character (A-Z, 0-9, _, .)'
)
@app_commands.choices(filter=[
    app_commands.Choice(name='Letters', value='letters'),
    app_commands.Choice(name='Numbers', value='numbers'),
    app_commands.Choice(name='Characters', value='characters'),
])
async def users_available(interaction: discord.Interaction, filter: app_commands.Choice[str], length: int, starts_with: str = '', ends_with: str = ''):
    await interaction.response.defer(thinking=True)
    await db.init()
    if length < 3 or length > 5:
        await interaction.followup.send('⚠️ Length must be between 3 and 5.')
        return
    combos = generate_filtered(filter.value, length, starts_with or '', ends_with or '')
    if not combos:
        await interaction.followup.send('⚠️ No combinations found for given filters.')
        return
    sample = random.sample(combos, min(40, len(combos)))
    available = []
    unavailable = []
    for name in sample:
        ok, err = await check_username_availability(name, BOT_TOKEN)
        if ok:
            available.append(name)
        else:
            unavailable.append(name)
            await db.add_tracked(interaction.guild_id, interaction.channel_id, name, int(time.time()))
        if len(available) >= 3:
            break
        await asyncio.sleep(0.5)
    embed = discord.Embed(title='Spectre Username Scanner ⚡', description='', color=discord.Color.from_rgb(30,31,34))
    if available:
        embed.add_field(name='✅ Available', value='\n'.join(f'`{n}`' for n in available), inline=False)
    else:
        embed.add_field(name='❌ Available', value='No usernames currently available for those filters.', inline=False)
    embed.add_field(name='📦 Added to tracking', value=f'{len(unavailable)} usernames are now being monitored.', inline=False)
    embed.set_footer(text=f'Filter: {filter.name} | Length: {length} | Showing up to 3 available')
    await interaction.followup.send(embed=embed)

@client.event
async def on_ready():
    await db.init()
    await tree.sync()
    logger.info(f'Logged in as {client.user} (id={client.user.id})')
    client.loop.create_task(notify.start_notifier(client, db))
    client.loop.create_task(auto_generate_task())

if __name__ == '__main__':
    client.run(BOT_TOKEN)
