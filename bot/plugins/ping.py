# (c) @AbirHasan2005

from bot import Client
from pyrogram import filters
from pyrogram.types import Message


@Client.on_message(filters.command(["start", "ping"]) & ~filters.edited)
async def ping_handler(_, m: Message):
    await m.reply_text("Hi, I am Rename Bot!")
