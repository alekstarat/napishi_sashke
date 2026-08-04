from app.auth.service import AuthService
from app.protocol.client import GetPublicKeyRequest
from app.handlers.base import PacketContext, PacketHandler
from app.protocol.sender import sender
from app.protocol.server import PublicKeyResponse, PublicKeyPayload


class GetPublicKeyHandler(PacketHandler[GetPublicKeyRequest]):
    packet_type = GetPublicKeyRequest

    def __init__(self, auth_service: AuthService) -> None:
        self._auth_service = auth_service

    async def handle(
        self,
        ctx: PacketContext,
        packet: GetPublicKeyRequest,
    ) -> None:

        public_key = await self._auth_service.get_public_key(
            packet.payload.username
        )

        await ctx.websocket.send_json(
            PublicKeyResponse(
                payload=PublicKeyPayload(
                    username=packet.payload.username,
                    public_key=public_key
                )
            ).model_dump()
        )