from fastapi import WebSocket

from .server import ServerPacket


class PacketSender:
    async def send(
        self,
        websocket: WebSocket,
        packet: ServerPacket,
    ) -> None:
        await websocket.send_json(packet.model_dump(mode="json"))


sender = PacketSender()