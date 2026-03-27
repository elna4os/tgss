import logging

import aiohttp
import config
from qdrant_client import AsyncQdrantClient
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (Application, ApplicationBuilder, CommandHandler,
                          ContextTypes)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def make_post_link(channel_id: int, post_id: int) -> str:
    cid = str(abs(channel_id))
    if cid.startswith("100"):
        cid = cid[3:]

    return f"https://t.me/c/{cid}/{post_id}"


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Process the search query
    query = " ".join(context.args) if context.args else ""
    if not query.strip():
        await update.message.reply_text("Usage: /search <query>")
        return

    # Check user membership
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(config.CHANNEL_ID, user_id)
    except Exception as e:
        logger.warning("Membership check failed for user %d: %s", user_id, e)
        await update.message.reply_text("Could not verify your channel membership. Please try again later.")
        return
    if member.status in (ChatMemberStatus.BANNED, ChatMemberStatus.LEFT):
        await update.message.reply_text("Access denied: you are not a member of the channel.")
        return

    # Embed the query
    http = context.bot_data["http"]
    qdrant = context.bot_data["qdrant"]
    try:
        async with http.post(
            f"{config.EMBEDDER_URL}/embed/text",
            params={"text": query.strip()},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            vector = data["embedding"]
    except Exception as e:
        logger.error("Embedding failed: %s", e)
        await update.message.reply_text("Search is temporarily unavailable. Please try again later.")
        return

    # Search in database
    try:
        results = await qdrant.query_points(
            collection_name=config.QDRANT_COLLECTION,
            query=vector,
            limit=config.SEARCH_LIMIT,
            with_payload=True,
        )
        hits = results.points
    except Exception as e:
        logger.error("Qdrant search failed: %s", e)
        await update.message.reply_text("Search is temporarily unavailable. Please try again later.")
        return
    if not hits:
        await update.message.reply_text("No results found.")
        return

    # Process results
    seen = set()
    links = []
    for hit in hits:
        post_id = hit.payload.get("post_id")
        chat_id = hit.payload.get("chat_id", config.CHANNEL_ID)
        if post_id and post_id not in seen:
            seen.add(post_id)
            links.append(make_post_link(chat_id, post_id))

    await update.message.reply_text("\n".join(links))


async def init_resources(app: Application) -> None:
    app.bot_data["http"] = aiohttp.ClientSession()
    app.bot_data["qdrant"] = AsyncQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)


def main() -> None:
    app = ApplicationBuilder().token(config.BOT_TOKEN).post_init(init_resources).build()
    app.add_handler(CommandHandler("search", search_command))
    logger.info("Bot is running")
    app.run_polling()


if __name__ == "__main__":
    main()
