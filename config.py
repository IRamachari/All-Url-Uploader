import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Config:
    # ── Telegram API ──────────────────────────────────────────────
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # ── Access control ────────────────────────────────────────────
    OWNER_ID = int(os.environ.get("OWNER_ID", 0))
    AUTH_USERS = set(
        int(x)
        for x in os.environ.get("AUTH_USERS", "").split()
        if x.strip().lstrip("-").isdigit()
    )

    # ── Paths & limits ────────────────────────────────────────────
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads/")
    MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 2 * 1024 * 1024 * 1024))  # 2 GB

    @classmethod
    def validate(cls) -> bool:
        """Return True if the mandatory env-vars are present."""
        ok = True
        if not cls.API_ID:
            logger.error("API_ID is missing!")
            ok = False
        if not cls.API_HASH:
            logger.error("API_HASH is missing!")
            ok = False
        if not cls.BOT_TOKEN:
            logger.error("BOT_TOKEN is missing!")
            ok = False
        return ok
