from app.protocol.server import (
    ErrorPayload,
    ErrorResponse,
)
from app.protocol.sender import sender

from .base import PacketContext


async def send_error(
    ctx: PacketContext,
    message: str,
) -> None:

    await sender.send(
        ctx.websocket,
        ErrorResponse(
            payload=ErrorPayload(
                message=message,
            )
        ),
    )