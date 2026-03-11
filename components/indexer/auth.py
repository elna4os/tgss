"""
Run this script once locally to create a Telethon user session:

    cd components/bot
    API_ID=<your_api_id> API_HASH=<your_api_hash> SESSION_PATH=../../session/tgss python auth.py

It will prompt for your phone number and the confirmation code.
After that, session/tgss.session will be created — it is mounted into the Docker container automatically.
"""

import asyncio
import os

from telethon import TelegramClient

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_PATH = os.getenv("SESSION_PATH", "../../session/tgss")

os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)


async def main():
    """Main entry point for the authentication script."""

    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        me = await client.get_me()
        print(f"Logged in as: {me.username or me.first_name} (id={me.id})")
        print(f"Session saved to: {SESSION_PATH}.session")

asyncio.run(main())
