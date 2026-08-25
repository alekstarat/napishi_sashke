from pathlib import Path

from handlers.base import PacketContext, PacketHandler
from protocol import ReceiveMessageEvent


class MessageHandler(PacketHandler[ReceiveMessageEvent]):

    packet_type = ReceiveMessageEvent

    async def handle(
        self,
        ctx: PacketContext,
        packet: ReceiveMessageEvent,
    ) -> None:

        text = packet.payload.text
        file_id = packet.payload.file_id
        media_type = packet.payload.media_type

        if ctx.client.peer_public_key is not None and text:
            text = ctx.client.crypto.try_decrypt(
                text,
                ctx.client.peer_public_key
            )

        media_path: Path | None = None

        if file_id and media_type and ctx.client.peer_public_key is not None:
            try:
                dest_dir = Path(__file__).parent.parent / "cache" / "decrypted"
                ext = {
                    "photo": ".jpg",
                    "video": ".mp4",
                    "audio": ".ogg",
                    "voice": ".ogg",
                }.get(media_type, "")
                dest = dest_dir / f"{file_id}{ext}"
                await ctx.client.file_service.download_file(
                    file_id,
                    dest,
                    ctx.client.peer_public_key,
                )
                media_path = dest
                ctx.ui.info(f"Saved {media_type} → {dest}")
            except Exception as e:
                # fallback: show error as text
                err = f"[{media_type}] (download failed: {e})"
                if text:
                    text = f"{err}\n{text}"
                else:
                    text = err

        ctx.ui.message_with_media(
            sender=packet.payload.sender,
            text=text or "",
            timestamp=packet.payload.timestamp,
            media_path=media_path,
            media_type=media_type,
        )
