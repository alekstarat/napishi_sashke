from typing import Any

from handlers.base import PacketContext, PacketHandler


class PacketDispatcher:
    def __init__(
        self,
        handlers: dict[type, PacketHandler],
    ) -> None:
        self._handlers = handlers

    def register(
        self,
        handler: PacketHandler,
    ) -> None:
        self._handlers[handler.packet_type] = handler

    async def dispatch(
        self,
        ctx: PacketContext,
        packet: Any,
    ) -> None:
        handler = self._handlers.get(type(packet))

        if handler is None:
            ctx.ui.error(
                f"No handler registered for {type(packet).__name__}"
            )
            return

        await handler.handle(
            ctx,
            packet,
        )