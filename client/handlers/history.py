from pathlib import Path

from protocol.models import HistoryResponse
from handlers.base import PacketHandler, PacketContext


class HistoryHandler(PacketHandler[HistoryResponse]):
    packet_type = HistoryResponse

    async def handle(self,
                     ctx: PacketContext,
                     packet: HistoryResponse):
        ctx.ui.reset_group()
        companion = packet.payload.companion

        for m in packet.payload.messages:

            text = m.text
            file_id = m.file_id
            media_type = m.media_type

            if ctx.client.peer_public_key is not None and text:
                text = ctx.client.crypto.try_decrypt(text, ctx.client.peer_public_key)

            media_path: Path | None = None

            if file_id and media_type and ctx.client.peer_public_key is not None:
                try:
                    dest_dir = Path(__file__).parent.parent / "cache" / "decrypted"
                    ext = {
                        "photo": ".jpg",
                        "audio": ".ogg",
                        "voice": ".ogg",
                    }.get(media_type, "")
                    dest = dest_dir / f"{file_id}{ext}"
                    if not dest.exists():
                        await ctx.client.file_service.download_file(
                            file_id,
                            dest,
                            ctx.client.peer_public_key,
                        )
                    media_path = dest
                except Exception as e:
                    err = f"[{media_type}] (download failed: {e})"
                    if text:
                        text = f"{err}\n{text}"
                    else:
                        text = err

            if m.sender == ctx.client.me:
                ctx.ui.own_message_with_media(
                    to=companion,
                    text=text or "",
                    media_path=media_path,
                    media_type=media_type,
                    timestamp=m.timestamp,
                )
            else:
                ctx.ui.message_with_media(
                    sender=m.sender,
                    text=text or "",
                    timestamp=m.timestamp,
                    media_path=media_path,
                    media_type=media_type,
                )
