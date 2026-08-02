from app.handlers.base import PacketContext, PacketHandler
from app.protocol.client import SendMessageRequest
from app.services.message import MessageService
from app.protocol.server import (
    SendMessageResponse,
    SendMessagePayload, HistoryEvent, HistoryPayload, HistoryMessage,
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
        )

        # history = await self._message_service.get_history(
        #     ctx.user,
        #     packet.payload.to,
        # )
        #
        # await sender.send(
        #     HistoryEvent(
        #         payload=HistoryPayload(
        #             messages=[
        #                 HistoryMessage(
        #                     id=message.uuid,
        #                     sender=message.sender.username,
        #                     recipient=message.recipient.username,
        #                     text=message.text,
        #                     timestamp=int(message.timestamp.timestamp())
        #                 )
        #                 for message in history
        #             ]
        #         )
        #     ).model_dump()
        # )

        await sender.send(
            ctx.websocket,
            SendMessageResponse(
                payload=SendMessagePayload(
                    id=message.uuid,
                )
            ),
        )

