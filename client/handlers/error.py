from handlers.base import PacketContext, PacketHandler
from protocol import ErrorResponse


class ErrorHandler(PacketHandler[ErrorResponse]):

    packet_type = ErrorResponse

    async def handle(
        self,
        ctx: PacketContext,
        packet: ErrorResponse,
    ) -> None:

        ctx.ui.error(
            packet.payload.message,
        )