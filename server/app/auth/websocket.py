import asyncio
import logging

from fastapi import WebSocket
from pydantic import ValidationError

from app.handlers.base import PacketContext
from app.protocol import parser
from app.protocol.client import AuthRequest
from app.services.connection import ConnectionService
from app.services.security import SecurityService

from .exceptions import AuthenticationError, InvalidPacket, InvalidToken
from .service import AuthService

logger = logging.getLogger("napishi.auth")


class WebSocketAuthenticator:
    def __init__(
        self,
        auth_service: AuthService,
        connections: ConnectionService,
        security: SecurityService,
    ) -> None:
        self._auth_service = auth_service
        self._connections = connections
        self._security = security

    async def authenticate(
        self,
        websocket: WebSocket,
        client_ip: str,
    ) -> PacketContext:
        timeout = self._security.settings.auth_timeout_seconds

        try:
            raw_packet = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=timeout,
            )
        except asyncio.TimeoutError as exc:
            await self._security.report_failure(client_ip, reason="auth timeout")
            raise InvalidPacket("auth timeout") from exc
        except Exception as exc:
            await self._security.report_failure(client_ip, reason="bad packet receive")
            raise InvalidPacket() from exc

        try:
            packet = parser.parse(raw_packet)
        except ValidationError as exc:
            await self._security.report_failure(client_ip, reason="invalid auth packet")
            raise InvalidPacket() from exc

        if not isinstance(packet, AuthRequest):
            await self._security.report_failure(client_ip, reason="first packet is not auth")
            raise InvalidPacket()

        try:
            user = await self._auth_service.authenticate(
                packet.payload.token,
                packet.payload.public_key,
            )
        except InvalidToken:
            await self._security.report_failure(client_ip, reason="invalid token")
            raise
        except AuthenticationError:
            await self._security.report_failure(client_ip, reason="auth rejected")
            raise

        await self._connections.register(
            user.username,
            websocket,
        )

        logger.info("AUTH ok user=%s ip=%s", user.username, client_ip)

        return PacketContext(
            user=user,
            websocket=websocket,
            connections=self._connections,
            client_ip=client_ip,
        )
