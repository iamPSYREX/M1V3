# (c) @AbirHasan2005

import time
import traceback
from bot import Client
from pyrogram import (
    filters,
    raw,
    utils
)
from pyrogram.file_id import FileId
from pyrogram.types import Message
from bot.core.file_info import (
    get_media_file_id,
    get_media_file_size,
    get_media_file_name
)
from configs import Config
from bot.core.display import progress_for_pyrogram


@Client.on_message(filters.command(["rename", "r"]) & ~filters.edited)
async def rename_handler(c: Client, m: Message):
    # Checks
    if (not m.reply_to_message) or (not m.reply_to_message.document):
        return await m.reply_text("Reply to any document to rename it!", quote=True)

    # Proceed
    editable = await m.reply_text("Now send me new file name!", quote=True)
    user_input_msg: Message = await c.listen(m.chat.id, timeout=300)
    if user_input_msg.text is None:
        await editable.edit("Process Cancelled!")
        return await user_input_msg.continue_propagation()
    if user_input_msg.text and user_input_msg.text.startswith("/"):
        await editable.edit("Process Cancelled!")
        return await user_input_msg.continue_propagation()
    if user_input_msg.text.rsplit(".", 1)[-1].lower() != get_media_file_name(m.reply_to_message).rsplit(".", 1)[-1].lower():
        file_name = user_input_msg.text.rsplit(".", 1)[0] + "." + get_media_file_name(m.reply_to_message).rsplit(".", 1)[-1].lower()
    else:
        file_name = user_input_msg.text
    await editable.edit("Please Wait ...")
    _c_file_id = FileId.decode(get_media_file_id(m.reply_to_message))
    try:
        c_time = time.time()
        file_id = await c.custom_upload(
            file_id=_c_file_id,
            file_size=get_media_file_size(m.reply_to_message),
            file_name=file_name,
            progress=progress_for_pyrogram,
            progress_args=(
                "Uploading ...\n"
                f"DC ID: {_c_file_id.dc_id}",
                editable,
                c_time
            )
        )
        # await editable.edit(f"{file_id}")

        media = raw.types.InputMediaUploadedDocument(
            mime_type=c.guess_mime_type(get_media_file_name(m.reply_to_message)) or "application/zip",
            file=file_id,
            force_file=None,
            thumb=None,
            attributes=[
                raw.types.DocumentAttributeFilename(file_name=file_name)
            ]
        )

        caption = "Dev - @AbirHasan2005"
        parse_mode = "Markdown"

        try:
            r = await c.send(
                raw.functions.messages.SendMedia(
                    peer=(await c.resolve_peer(m.chat.id)),
                    media=media,
                    silent=None,
                    reply_to_msg_id=None,
                    random_id=c.rnd_id(),
                    schedule_date=None,
                    reply_markup=None,
                    **await utils.parse_text_entities(c, caption, parse_mode, None)
                )
            )
        except Exception as _err:
            Config.LOGGER.getLogger(__name__).error(_err)
            Config.LOGGER.getLogger(__name__).info(f"{traceback.format_exc()}")
        else:
            await editable.edit("Uploaded Successfully!")
    except Exception as err:
        await editable.edit("Failed to Rename File!\n\n"
                            f"**Error:** `{err}`\n\n"
                            f"**Traceback:** `{traceback.format_exc()}`")
