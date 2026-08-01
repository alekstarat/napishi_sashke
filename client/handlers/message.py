from handlers.base import PacketContext, PacketHandler
from protocol import ReceiveMessageEvent


class MessageHandler(PacketHandler[ReceiveMessageEvent]):

    packet_type = ReceiveMessageEvent

    async def handle(
        self,
        ctx: PacketContext,
        packet: ReceiveMessageEvent,
    ) -> None:

        ctx.ui.message(
            sender=packet.payload.sender,
            text=packet.payload.text,
            timestamp=packet.payload.timestamp,
        )