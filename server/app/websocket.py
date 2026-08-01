from collections.abc import Awaitable, Callable
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(
            self,
            username: str,
            websocket: WebSocket
    ):
        await websocket.accept()
        self.connections[username] = websocket

    def disconnect(self, username: str):
        self.connections.pop(username, None)

    def is_online(self, username: str) -> bool:
        return username in self.connections

    async def send(
            self,
            username: str,
            data: dict
    ):
        websocket = self.connections.get(username)

        if websocket is None:
            return False

        await websocket.send_json(data)
        return True


manager = ConnectionManager()