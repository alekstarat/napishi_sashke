from handlers.base import PacketContext, PacketHandler
from protocol import SendMessageResponse


class SendOkHandler(PacketHandler[SendMessageResponse]):

    packet_type = SendMessageResponse

    async def handle(
        self,
        ctx: PacketContext,
        packet: SendMessageResponse,
    ) -> None:
        client = ctx.client
        if client._last_outgoing:
            to, text = client._last_outgoing
            client._last_outgoing = None
            ctx.ui.own_message(to=to, text=text)
        else:
            ctx.ui.success(f"Message sent")