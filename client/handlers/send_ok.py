from handlers.base import PacketContext, PacketHandler
from protocol import SendMessageResponse


class SendOkHandler(PacketHandler[SendMessageResponse]):

    packet_type = SendMessageResponse

    async def handle(
        self,
        ctx: PacketContext,
        packet: SendMessageResponse,
    ) -> None:

        ctx.ui.success(
            f"Message sent"
        )