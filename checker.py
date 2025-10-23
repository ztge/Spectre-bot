import aiohttp

DISCORD_API = "https://discord.com/api/v10"

async def check_username_availability(username: str, token: str):
    '''
    Returns (available: bool, error_message: str|None)
    Uses the /users endpoint search to see if a username exists publicly.
    '''
    headers = {"Authorization": f"Bot {token}"}
    params = {"q": username, "limit": 5}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{DISCORD_API}/users", headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list):
                        for u in data:
                            if u.get('username','').lower() == username.lower():
                                return False, None
                    elif isinstance(data, dict):
                        users = data.get('users') or data.get('data') or []
                        for u in users:
                            if u.get('username','').lower() == username.lower():
                                return False, None
                    return True, None
                else:
                    text = await resp.text()
                    return False, f'HTTP {resp.status}: {text}'
        except Exception as e:
            return False, str(e)
