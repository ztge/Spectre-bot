import discord
from datetime import datetime, timezone

def make_available_embed(username: str, guild_name: str = None):
    desc = f'Username `{username}` is now available!'
    embed = discord.Embed(
        title='Discord Status Update',
        description=desc,
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text='Spectre • Auto-checker')
    if guild_name:
        embed.add_field(name='Guild', value=guild_name, inline=True)
    return embed

def make_unavailable_embed(username: str, guild_name: str = None):
    desc = f'Username `{username}` is no longer available.'
    embed = discord.Embed(
        title='Discord Status Update',
        description=desc,
        color=discord.Color.dark_grey(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text='Spectre • Auto-checker')
    if guild_name:
        embed.add_field(name='Guild', value=guild_name, inline=True)
    return embed
