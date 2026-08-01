from app.handlers.base import PacketContext, PacketHandler

from .exceptions import send_error


class PacketDispatcher:

    def __init__(
        self,
        handlers: dict[type, PacketHandler],
    ):
        self._handlers = handlers


    async def dispatch(
        self,
        ctx: PacketContext,
        packet,
    ) -> None:

        handler = self._handlers.get(
            type(packet)
        )

        if handler is None:
            await send_error(
                ctx,
                "Unknown packet type",
            )
            return

        try:

            await handler.handle(
                ctx,
                packet,
            )

        except ValueError as exc:

            await send_error(
                ctx,
                str(exc),
            )

        except Exception as exc:

            import traceback

            traceback.print_exc()

            await send_error(
                ctx,
                str(exc),
            )