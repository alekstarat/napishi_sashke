from app.handlers.base import PacketContext, PacketHandler
from app.protocol.client import GetHistoryRequest
from app.protocol.server import (
    HistoryResponse,
    HistoryPayload,
    HistoryMessage,
)
from app.protocol.sender import sender
from app.services.message import MessageService


class GetHistoryHandler(PacketHandler[GetHistoryRequest]):
    packet_type = GetHistoryRequest

    def __init__(self, message_service: MessageService) -> None:
        self._message_service = message_service

    async def handle(
            self,
            ctx: PacketContext,
            packet: GetHistoryRequest
    ) -> None:
        messages = await self._message_service.get_history(
            user=ctx.user,
            companion_username=packet.payload.username
        )

        await sender.send(
            ctx.websocket,
            HistoryResponse(
                payload=HistoryPayload(
                    companion=packet.payload.username,
                    messages=[
                        HistoryMessage(
                            id=m.uuid,
                            sender=m.sender.username,
                            recipient=m.recipient.username,
                            text=m.text,
                            timestamp=int(m.timestamp.timestamp())
                        )
                        for m in messages
                    ]
                )
            )
        )