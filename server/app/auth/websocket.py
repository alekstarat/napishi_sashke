from fastapi import WebSocket
from pydantic import ValidationError

from app.handlers.base import PacketContext
from app.protocol import parser
from app.protocol.client import AuthRequest
from app.services.connection import ConnectionService

from .exceptions import InvalidPacket
from .service import AuthService


class WebSocketAuthenticator:
    def __init__(
        self,
        auth_service: AuthService,
        connections: ConnectionService,
    ) -> None:
        self._auth_service = auth_service
        self._connections = connections

    async def authenticate(
        self,
        websocket: WebSocket,
    ) -> PacketContext:
        try:
            raw_packet = await websocket.receive_json()

            packet = parser.parse(raw_packet)

        except ValidationError as exc:
            raise InvalidPacket() from exc

        if not isinstance(packet, AuthRequest):
            raise InvalidPacket()

        user = await self._auth_service.authenticate(
            packet.payload.token,
        )

        await self._connections.register(
            user.username,
            websocket
        )

        return PacketContext(
            user=user,
            websocket=websocket,
            connections=self._connections,
        )

