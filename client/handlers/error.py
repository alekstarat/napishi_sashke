from handlers.base import (
    PacketHandler,
    PacketContext
)

from protocol import ErrorResponse


class ErrorHandler(
    PacketHandler[ErrorResponse]
):

    packet_type = ErrorResponse

    async def handle(
            self,
            ctx: PacketContext,
            packet: ErrorResponse
    ) -> None:
        msg = packet.payload.message
        ctx.ui.error(msg)
        if ctx.client and not ctx.client._authenticated.is_set():
            ctx.client._authenticated.set()
