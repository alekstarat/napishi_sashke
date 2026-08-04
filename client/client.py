import asyncio
import json

import websockets
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from websockets.asyncio.client import ClientConnection

from handlers.base import PacketContext
from handlers.dispatcher import PacketDispatcher
from protocol import (
    AuthRequest,
    SendMessageRequest, AuthPayload
)
from prompt_toolkit.patch_stdout import patch_stdout

from protocol.models import GetHistoryRequest, GetHistoryPayload, PublicKeyRequest, PublicKeyPayload, PublicKeyResponse
from protocol.parser import parse_packet
from services.crypto import CryptoService
from ui.console import ConsoleUI
from ui.input import ConsoleInput
from commands import (
    CommandError,
    parse_line
)

class MessengerClient:

    def __init__(
        self,
        url: str,
        token: str,
        companion: str,
        dispatcher: PacketDispatcher,
    ) -> None:

        self.url = url
        self.token = token
        self.dispatcher = dispatcher

        self.me = "ты"

        self.ui = ConsoleUI()
        self.input = ConsoleInput()

        self.websocket: ClientConnection | None = None

        self._last_outgoing: tuple[str, str] | None = None
        self.companion = companion
        self._authenticated = asyncio.Event()
        self.crypto = CryptoService()
        self.peer_public_key: X25519PublicKey | None = None


    async def connect(self) -> None:

        self.websocket = await websockets.connect(
            self.url
        )

        self.ui.connected()


    async def authenticate(self) -> None:

        packet = AuthRequest(
            payload=AuthPayload(
                token=self.token,
                public_key=self.crypto.export_public_key()
            )
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
            client=self
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

    def _line_to_packet(self, line: str):
        result = parse_line(line, self.companion)

        if isinstance(result, tuple) and result[0] == "switch":
            self.companion = result[1]
            self.ui.system(f"Чат с {self.companion}")
            return GetHistoryRequest(
                payload=GetHistoryPayload(username=self.companion)
            )

        return result

    async def sender(self) -> None:
        await self._authenticated.wait()
        # await self._pick_companion()
        if self.companion:
            self.ui.reset_group()
            self.ui.system(f"Чат с {self.companion}")

            await self.send(
                PublicKeyRequest(
                    payload=PublicKeyPayload(
                        username=self.companion
                    )
                )
            )

        else:
            await self._pick_companion()

        while True:
            prompt = f"{self.companion} > " if self.companion else "you >"
            line = await self.input.read(prompt)
            if not line:
                continue

            print("\033[1A\033[2K", end="", flush=True)

            try:
                packet = self._line_to_packet(line)
            except CommandError as exc:
                self.ui.error(str(exc))
                continue

            if packet is None:
                continue

            if isinstance(packet, SendMessageRequest):
                if self.peer_public_key is None:
                    self.ui.error(
                        "Public key not received yet."
                    )
                    continue

                plaintext = packet.payload.text

                ciphertext = self.crypto.encrypt(
                    plaintext=plaintext,
                    peer_public_key=self.peer_public_key,
                )

                packet.payload.text = ciphertext

                packet = SendMessageRequest(
                    payload=packet.payload.model_copy(
                        update={
                            "text": ciphertext,
                        }
                    )
                )

                self._last_outgoing = (
                    packet.payload.to,
                    plaintext,
                )

            await self.send(packet)

    async def _pick_companion(self) -> None:
        while True:
            name = (await self.input.read("companion >")).strip()
            print("\033[1A\033[2K", end="", flush=True)

            if not name:
                continue
            if name.startswith("/"):
                self.ui.error("Введи имя собеседника")
                continue

            self.ui.reset_group()
            self.companion = name
            # self.ui.system(f"Чат с {name}")
            # await self.send(
            #     GetHistoryRequest(
            #         payload=GetHistoryPayload(username=name)
            #     )
            # )

            await self.sender()

            return

    async def run(self) -> None:

        self.ui.banner()

        await self.connect()
        await self.authenticate()

        with patch_stdout(raw=True):
            await asyncio.gather(
                self.receiver(),
                self.sender(),
            )