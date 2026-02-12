import asyncio
import sys
from config import Config, logger


async def main() -> None:
    # Validate before importing the client (avoids cryptic errors)
    if not Config.validate():
        logger.critical("Configuration is incomplete — exiting.")
        sys.exit(1)

    from bot import app
    from pyrogram import idle          # pyrofork exposes idle() here

    try:
        await app.start()
        logger.info("Bot started successfully.  Press Ctrl+C to stop.")
        await idle()
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
    finally:
        if app.is_connected:
            await app.stop()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    # Python 3.10+ compatible entry-point
    asyncio.run(main())
