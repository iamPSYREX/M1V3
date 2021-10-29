# (c) @AbirHasan2005

import os
import io
import math
import inspect
import functools
from typing import Union
from pyromod import listen
from pyrogram import raw
from pyrogram import utils
from pyrogram import StopTransmission
from pyrogram import Client as RawClient
from pyrogram.errors import (
    AuthBytesInvalid
)
from pyrogram.file_id import (
    FileId,
    FileType,
    ThumbnailSource
)
from pyrogram.storage import Storage
from pyrogram.session import (
    Auth,
    Session
)
from configs import Config
from bot.core.fixes import (
    chunk_size,
    offset_fix
)

LOGGER = Config.LOGGER
log = LOGGER.getLogger(__name__)


class Client(RawClient):
    """ Custom Bot Class """

    def __init__(self, session_name: Union[str, Storage] = "RenameBot"):
        super().__init__(
            session_name,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(
                root="bot/plugins"
            )
        )

    async def start(self):
        await super().start()
        print("Bot Started!")

    async def stop(self, *args):
        await super().stop()
        print("Bot Stopped!")

    async def custom_upload(
        self,
        file_id: FileId,
        file_size: int,
        file_name: str,
        progress: callable,
        progress_args: tuple = ()
    ):
        dc_id = file_id.dc_id

        async with self.media_sessions_lock:
            session = self.media_sessions.get(dc_id, None)

            if session is None:
                if dc_id != await self.storage.dc_id():
                    session = Session(
                        self, dc_id, await Auth(self, dc_id, await self.storage.test_mode()).create(),
                        await self.storage.test_mode(), is_media=True
                    )
                    await session.start()

                    for _ in range(3):
                        exported_auth = await self.send(
                            raw.functions.auth.ExportAuthorization(
                                dc_id=dc_id
                            )
                        )

                        try:
                            await session.send(
                                raw.functions.auth.ImportAuthorization(
                                    id=exported_auth.id,
                                    bytes=exported_auth.bytes
                                )
                            )
                        except AuthBytesInvalid:
                            continue
                        else:
                            break
                    else:
                        await session.stop()
                        raise AuthBytesInvalid
                else:
                    session = Session(
                        self, dc_id, await self.storage.auth_key(),
                        await self.storage.test_mode(), is_media=True
                    )
                    await session.start()

                self.media_sessions[dc_id] = session

        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id,
                    access_hash=file_id.chat_access_hash
                )
            else:
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(
                        chat_id=-file_id.chat_id
                    )
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash
                    )

            location = raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG
            )
        elif file_type == FileType.PHOTO:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size
            )
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size
            )

        part_size = 512 * 1024
        file_part = 0
        new_file_id = self.rnd_id()
        limit = 1024 * 1024
        offset = 0
        file_total_parts = int(math.ceil(file_size / part_size))

        try:
            r = await session.send(
                raw.functions.upload.GetFile(
                    location=location,
                    offset=offset,
                    limit=limit
                ),
                sleep_threshold=30
            )

            if isinstance(r, raw.types.upload.File):
                while True:
                    chunk = r.bytes
                    if not chunk:
                        break

                    fp = io.BytesIO(chunk)
                    fp.seek(0, os.SEEK_END)
                    fp.seek(0)

                    offset += limit

                    # Outputs
                    log.info("\n"
                             f"Part Number ------> {file_part}\n"
                             f"Total Parts ------> {file_total_parts}\n"
                             f"Limit ------------> {limit}\n"
                             f"Offset Number ----> {offset}")

                    with fp:
                        file_part_ = 0
                        fp.seek(part_size * file_part_)

                        while True:
                            chunk_ = fp.read(part_size)
                            rpc = raw.functions.upload.SaveBigFilePart(
                                file_id=new_file_id,
                                file_part=file_part,
                                file_total_parts=file_total_parts,
                                bytes=chunk_
                            )
                            if not chunk_:
                                break

                            file_part_ += 1
                            file_part += 1

                    if progress:
                        func = functools.partial(
                            progress,
                            min(offset, file_size)
                            if file_size != 0
                            else offset,
                            file_size,
                            *progress_args
                        )

                        if inspect.iscoroutinefunction(progress):
                            await func()
                        else:
                            await self.loop.run_in_executor(self.executor, func)

                    r = await session.send(
                        raw.functions.upload.GetFile(
                            location=location,
                            offset=offset,
                            limit=limit
                        ),
                        sleep_threshold=30
                    )

                    if len(chunk) < limit:
                        break

        except Exception as e:
            if not isinstance(e, StopTransmission):
                log.error(e, exc_info=True)

            return False
        else:
            return raw.types.InputFileBig(
                id=new_file_id,
                parts=file_total_parts,
                name=file_name
            )
