from protocol.models import HistoryResponse
from handlers.base import PacketHandler, PacketContext

class HistoryHandler(PacketHandler[HistoryResponse]):
    packet_type = HistoryResponse

    async def handle(self,
                     ctx: PacketContext,
                     packet: HistoryResponse):
        ctx.ui.reset_group()
        companion = packet.payload.companion
        # ctx.ui.system(f"История с {companion}")

        for m in packet.payload.messages:

            text = m.text

            if ctx.client.peer_public_key is not None:
                text = ctx.client.crypto.try_decrypt(text, ctx.client.peer_public_key)

            if m.sender == ctx.client.me:
                ctx.ui.own_message(to=companion, text=text)
            else:
                ctx.ui.message(
                    sender=m.sender,
                    text=text,
                    timestamp=m.timestamp
                )