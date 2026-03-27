"""
Run this script once locally to create a Telethon user session:

    cd components/indexer
    python auth.py

It will prompt for your phone number and the confirmation code.
After that, session/tgss.session will be created — it is mounted into the Docker container automatically.
"""

import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_PATH = os.getenv("SESSION_PATH", "./session/tgss")

os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)


async def main():
    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        me = await client.get_me()
        print(f"Logged in as: {me.username or me.first_name} (id={me.id})")
        print(f"Session saved to: {SESSION_PATH}.session")

asyncio.run(main())
