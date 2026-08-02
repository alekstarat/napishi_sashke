from protocol.models import HistoryResponse
from handlers.base import PacketHandler, PacketContext

class HistoryHandler(PacketHandler[HistoryResponse]):
    packet_type = HistoryResponse

    async def handle(self,
                     ctx: PacketContext,
                     packet: HistoryResponse):
        companion = packet.payload.companion
        ctx.ui.system(f"История с {companion}")
        for m in packet.payload.messages:
            ctx.ui.message(
                sender=m.sender,
                text=m.text,
                timestamp=m.timestamp
            )