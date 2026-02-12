from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from config import Config

START_TEXT = (
    "👋 **Hi {mention}!**\n\n"
    "I can upload files to Telegram from any direct URL.\n\n"
    "Just send me a link and I'll do the rest.\n\n"
    "**Supported:** Direct URLs, redirect URLs"
)

HELP_TEXT = (
    "**How to use:**\n\n"
    "1. Send me a direct download URL.\n"
    "2. I'll download the file and upload it here.\n\n"
    "**Commands:**\n"
    "/start  — Start the bot\n"
    "/help   — Show this message\n"
    "/about  — About this bot"
)

ABOUT_TEXT = (
    "**All URL Uploader Bot**\n\n"
    "**Language:** Python 3.11\n"
    "**Framework:** Pyrofork (Pyrogram fork)\n"
    "**Source:** [GitHub](https://github.com/kalanakt/All-Url-Uploader)"
)

BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Help", callback_data="help"),
            InlineKeyboardButton("About", callback_data="about"),
        ],
        [
            InlineKeyboardButton("Close", callback_data="close"),
        ],
    ]
)

BACK_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("⬅ Back", callback_data="home")]]
)


@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    await message.reply_text(
        START_TEXT.format(mention=message.from_user.mention),
        reply_markup=BUTTONS,
        disable_web_page_preview=True,
    )


@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply_text(
        HELP_TEXT,
        reply_markup=BACK_BUTTON,
        disable_web_page_preview=True,
    )


@Client.on_message(filters.command("about") & filters.private)
async def about_command(client: Client, message: Message):
    await message.reply_text(
        ABOUT_TEXT,
        reply_markup=BACK_BUTTON,
        disable_web_page_preview=True,
    )


@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data

    if data == "home":
        await query.message.edit_text(
            START_TEXT.format(mention=query.from_user.mention),
            reply_markup=BUTTONS,
            disable_web_page_preview=True,
        )
    elif data == "help":
        await query.message.edit_text(
            HELP_TEXT,
            reply_markup=BACK_BUTTON,
            disable_web_page_preview=True,
        )
    elif data == "about":
        await query.message.edit_text(
            ABOUT_TEXT,
            reply_markup=BACK_BUTTON,
            disable_web_page_preview=True,
        )
    elif data == "close":
        await query.message.delete()

    await query.answer()
