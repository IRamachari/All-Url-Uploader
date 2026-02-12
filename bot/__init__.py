import os
from pyrogram import Client          # ← resolved by pyrofork at runtime
from config import Config, logger

# Make sure the download directory exists
os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)

app = Client(
    name="all-url-uploader",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="bot/plugins"),
    in_memory=True,                  # no session file on disk
    max_concurrent_transmissions=3,  # avoid flood-waits
)

logger.info("Bot client initialized.")
