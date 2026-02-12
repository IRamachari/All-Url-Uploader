import os
import re
import time
import asyncio
import traceback
from urllib.parse import unquote, urlparse

import aiohttp
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageNotModified

from config import Config, logger

# ── Helpers ───────────────────────────────────────────────────────────────

URL_REGEX = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE
)

PROGRESS_INTERVAL = 5  # seconds between progress-bar edits


def human_size(size: int | float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def filename_from_url(url: str) -> str:
    """Best-effort filename extraction from a URL."""
    path = urlparse(url).path
    name = os.path.basename(unquote(path)).strip()
    return name if name else "downloaded_file"


def filename_from_headers(headers: dict) -> str | None:
    cd = headers.get("Content-Disposition", "")
    if "filename=" in cd:
        # handles both filename="x" and filename=x
        parts = cd.split("filename=")[-1].strip().strip('"').strip("'")
        if parts:
            return parts
    return None


async def progress_callback(
    current: int,
    total: int,
    message: Message,
    start_time: float,
    last_edit: list,   # mutable container so we can update from closure
    action: str = "Uploading",
):
    """Edit the status message at most once every PROGRESS_INTERVAL seconds."""
    now = time.time()
    if now - last_edit[0] < PROGRESS_INTERVAL:
        return
    last_edit[0] = now

    elapsed = now - start_time
    speed = current / elapsed if elapsed > 0 else 0
    pct = current * 100 / total if total else 0

    text = (
        f"**{action}…**\n"
        f"`[{'█' * int(pct // 5)}{'░' * (20 - int(pct // 5))}]` {pct:.1f}%\n"
        f"**Done:** {human_size(current)} / {human_size(total)}\n"
        f"**Speed:** {human_size(speed)}/s"
    )
    try:
        await message.edit_text(text)
    except MessageNotModified:
        pass
    except FloodWait as fw:
        await asyncio.sleep(fw.value)


# ── Download ──────────────────────────────────────────────────────────────

async def download_file(
    url: str,
    dest: str,
    message: Message,
) -> tuple[str, int]:
    """
    Stream-download *url* into *dest*, updating *message* with progress.
    Returns (file_path, file_size).
    """
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=60)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, allow_redirects=True) as resp:
            if resp.status != 200:
                raise ValueError(
                    f"HTTP {resp.status} — {resp.reason}"
                )

            total = int(resp.headers.get("Content-Length", 0))
            fname = filename_from_headers(resp.headers) or filename_from_url(url)
            file_path = os.path.join(dest, fname)

            # Check Telegram file-size limit (~2 GB for bots)
            if total and total > Config.MAX_FILE_SIZE:
                raise ValueError(
                    f"File too large ({human_size(total)}). "
                    f"Telegram limit is {human_size(Config.MAX_FILE_SIZE)}."
                )

            start = time.time()
            last_edit = [0.0]
            downloaded = 0

            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    await f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        await progress_callback(
                            downloaded, total, message, start, last_edit,
                            action="Downloading",
                        )

    return file_path, downloaded


# ── Upload handler ────────────────────────────────────────────────────────

@Client.on_message(filters.regex(URL_REGEX) & filters.private)
async def url_upload(client: Client, message: Message):
    url = message.text.strip().split()[0]  # first URL in the message

    status = await message.reply_text("**🔍 Checking URL…**")

    try:
        # ── 1. Download ──────────────────────────────────────────
        await status.edit_text("**⬇️ Downloading…**")
        file_path, file_size = await download_file(
            url, Config.DOWNLOAD_DIR, status
        )

        # ── 2. Upload to Telegram ────────────────────────────────
        await status.edit_text("**⬆️ Uploading to Telegram…**")
        start = time.time()
        last_edit = [0.0]

        try:
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=f"**{os.path.basename(file_path)}**\n"
                        f"**Size:** {human_size(file_size)}",
                progress=progress_callback,
                progress_args=(status, start, last_edit, "Uploading"),
            )
        except FloodWait as fw:
            logger.warning("FloodWait: sleeping %s s", fw.value)
            await asyncio.sleep(fw.value)
            # retry once
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=f"**{os.path.basename(file_path)}**\n"
                        f"**Size:** {human_size(file_size)}",
            )

        await status.edit_text("**✅ Upload complete!**")

    except ValueError as ve:
        await status.edit_text(f"**❌ Error:** {ve}")
        logger.warning("ValueError for %s: %s", url, ve)

    except aiohttp.ClientError as ce:
        await status.edit_text(
            f"**❌ Connection error:**\n`{ce}`\n\nMake sure the URL is valid."
        )
        logger.exception("aiohttp error for %s", url)

    except Exception:
        tb = traceback.format_exc()
        logger.exception("Unhandled error for %s", url)
        await status.edit_text(
            f"**❌ Something went wrong:**\n```\n{tb[-1000:]}\n```"
        )

    finally:
        # Clean up downloaded file
        try:
            if "file_path" in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
