from app.handlers.base import PacketContext, PacketHandler
from app.protocol.client import PingRequest
from app.protocol.server import PongResponse
from app.protocol.sender import sender


class PingHandler(PacketHandler[PingRequest]):

    packet_type = PingRequest

    async def handle(
        self,
        ctx: PacketContext,
        packet: PingRequest,
    ) -> None:

        await sender.send(
            ctx.websocket,
            PongResponse(),
        )