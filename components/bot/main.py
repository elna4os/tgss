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
    """Generate a link to a specific post in a Telegram channel.

    Args:
        channel_id (int): The unique identifier of the Telegram channel. For private channels, this is a negative number.
        post_id (int): The unique identifier of the post within the channel.

    Returns:
        str: A URL linking directly to the specified post.
    """

    cid = str(abs(channel_id))
    if cid.startswith("100"):
        cid = cid[3:]

    return f"https://t.me/c/{cid}/{post_id}"


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /search command.

    Args:
        update (Update): The update object representing the incoming message and its context.
        context (ContextTypes.DEFAULT_TYPE): The context object providing access to the bot and other shared data.
    """

    query = " ".join(context.args) if context.args else ""
    if not query.strip():
        await update.message.reply_text("Usage: /search <query>")
        return

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

    http: aiohttp.ClientSession = context.bot_data["http"]
    qdrant: AsyncQdrantClient = context.bot_data["qdrant"]

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

    try:
        # Overfetch to account for multiple parts per post
        results = await qdrant.query_points(
            collection_name=config.QDRANT_COLLECTION,
            query=vector,
            limit=config.SEARCH_LIMIT * 3,
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

    # Deduplicate by post_id, preserving relevance order
    seen = set()
    links = []
    for hit in hits:
        post_id = hit.payload.get("post_id")
        chat_id = hit.payload.get("chat_id", config.CHANNEL_ID)
        if post_id and post_id not in seen:
            seen.add(post_id)
            links.append(make_post_link(chat_id, post_id))
            if len(links) >= config.SEARCH_LIMIT:
                break

    await update.message.reply_text("\n".join(links))


async def post_init(app: Application) -> None:
    """Initialize resources for the bot.

    Args:
        app (Application): The application instance.
    """

    app.bot_data["http"] = aiohttp.ClientSession()
    app.bot_data["qdrant"] = AsyncQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)


def main() -> None:
    app = ApplicationBuilder().token(config.BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("search", search_command))

    logger.info("Bot is running")
    app.run_polling()


if __name__ == "__main__":
    main()
