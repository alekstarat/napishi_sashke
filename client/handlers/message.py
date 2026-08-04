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

        if ctx.client.peer_public_key is not None:
            text = ctx.client.crypto.try_decrypt(
                text,
                ctx.client.peer_public_key
            )

        ctx.ui.message(
            sender=packet.payload.sender,
            text=text,
            timestamp=packet.payload.timestamp,
        )