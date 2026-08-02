import asyncio
import json

import websockets
from websockets.asyncio.client import ClientConnection

from handlers.base import PacketContext
from handlers.dispatcher import PacketDispatcher
from protocol import (
    AuthRequest,
)
from protocol.parser import parse_packet
from ui.console import ConsoleUI
from ui.input import ConsoleInput
from commands import (
    CommandError,
    parse_command
)

class MessengerClient:

    def __init__(
        self,
        url: str,
        token: str,
        dispatcher: PacketDispatcher,
    ) -> None:

        self.url = url
        self.token = token
        self.dispatcher = dispatcher

        self.ui = ConsoleUI()
        self.input = ConsoleInput()

        self.websocket: ClientConnection | None = None


    async def connect(self) -> None:

        self.websocket = await websockets.connect(
            self.url
        )

        self.ui.connected()


    async def authenticate(self) -> None:

        packet = AuthRequest(
            payload={
                "token": self.token,
            }
        )

        await self.send(
            packet
        )


    async def send(
        self,
        packet,
    ) -> None:

        if self.websocket is None:
            raise RuntimeError(
                "Not connected"
            )

        await self.websocket.send(
            packet.model_dump_json()
        )


    async def receiver(self) -> None:

        assert self.websocket is not None

        ctx = PacketContext(
            websocket=self.websocket,
            ui=self.ui,
        )

        while True:

            raw = await self.websocket.recv()

            data = json.loads(raw)

            packet = parse_packet(
                data
            )

            await self.dispatcher.dispatch(
                ctx,
                packet,
            )

    async def sender(
            self,
    ) -> None:

        while True:

            command = await self.input.read(
                self.ui.prompt()
            )

            if not command:
                continue

            try:
                packet = parse_command(
                    command,
                )

            except CommandError as exc:
                self.ui.error(
                    str(exc),
                )
                continue

            await self.send(
                packet,
            )


    async def run(self) -> None:

        self.ui.banner()

        await self.connect()

        await self.authenticate()

        await asyncio.gather(
            self.receiver(),
            self.sender(),
        )