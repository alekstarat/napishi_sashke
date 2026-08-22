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

            display = text or ""

            if file_id and media_type and ctx.client.peer_public_key is not None:
                try:
                    dest_dir = Path(__file__).parent.parent / "cache" / "decrypted"
                    ext = {
                        "photo": ".jpg",
                        "video": ".mp4",
                        "audio": ".ogg",
                    }.get(media_type, "")
                    dest = dest_dir / f"{file_id}{ext}"
                    if not dest.exists():
                        await ctx.client.file_service.download_file(
                            file_id,
                            dest,
                            ctx.client.peer_public_key,
                        )
                    label = f"[{media_type}] {dest.name}"
                    if text:
                        display = f"{label}\n{text}"
                    else:
                        display = label
                except Exception as e:
                    display = f"[{media_type}] (download failed: {e})"
                    if text:
                        display = f"{display}\n{text}"

            if m.sender == ctx.client.me:
                ctx.ui.own_message(to=companion, text=display)
            else:
                ctx.ui.message(
                    sender=m.sender,
                    text=display,
                    timestamp=m.timestamp
                )