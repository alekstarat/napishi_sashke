from app.handlers.base import PacketContext, PacketHandler
from app.protocol.client import SendMessageRequest
from app.services.message import MessageService
from app.protocol.server import (
    SendMessageResponse,
    SendMessagePayload
)
from app.protocol.sender import sender

class SendMessageHandler(
    PacketHandler[SendMessageRequest]
):

    packet_type = SendMessageRequest

    def __init__(
        self,
        message_service: MessageService,
    ) -> None:
        self._message_service = message_service

    async def handle(
            self,
            ctx: PacketContext,
            packet: SendMessageRequest,
    ) -> None:
        message = await self._message_service.send(
            sender=ctx.user,
            recipient=packet.payload.to,
            text=packet.payload.text,
            file_id=packet.payload.file_id,
            media_type=packet.payload.media_type
        )

        await sender.send(
            ctx.websocket,
            SendMessageResponse(
                payload=SendMessagePayload(
                    id=message.uuid,
                )
            ),
        )

