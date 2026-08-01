from handlers.base import (
    PacketHandler,
    PacketContext
)

from protocol import AuthResponse


class AuthHandler(
    PacketHandler[AuthResponse]
):

    packet_type = AuthResponse

    async def handle(
            self,
            ctx: PacketContext,
            packet: AuthResponse
    ) -> None:

        ctx.ui.success(
            "Authenticated"
        )