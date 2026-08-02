from fastapi import WebSocket

from app.protocol import AuthResponse
from app.protocol.server import ServerPacket
from app.protocol.sender import sender


class ConnectionService:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(
        self,
        username: str,
        websocket: WebSocket,
    ) -> None:
        self._connections[username] = websocket

    def disconnect(
        self,
        username: str,
    ) -> None:
        self._connections.pop(username, None)

    def is_online(
        self,
        username: str,
    ) -> bool:
        return username in self._connections

    async def send(
        self,
        username: str,
        packet: ServerPacket,
    ) -> bool:
        websocket = self._connections.get(username)

        if websocket is None:
            return False

        await sender.send(
            websocket,
            packet,
        )

        return True

    def get(
        self,
        username: str,
    ) -> WebSocket | None:
        return self._connections.get(username)

    def count(self) -> int:
        return len(self._connections)

    async def register(
            self,
            username: str,
            websocket: WebSocket
    ) -> None:
        await self.connect(
            username,
            websocket
        )

        await sender.send(
            websocket,
            AuthResponse()
        )