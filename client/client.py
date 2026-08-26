import asyncio
import json
from pathlib import Path

import websockets
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PublicKey,
)
from websockets.asyncio.client import ClientConnection

from commands import (
    CommandError,
    parse_line,
)

from handlers.base import PacketContext
from handlers.dispatcher import PacketDispatcher

from protocol import (
    AuthPayload,
    AuthRequest,
    SendMessagePayload,
    SendMessageRequest,
)

from protocol.models import (
    GetHistoryPayload,
    GetHistoryRequest,
    PublicKeyPayload,
    PublicKeyRequest,
)

from protocol.parser import parse_packet

from prompt_toolkit.patch_stdout import patch_stdout

from services.crypto import CryptoService
from services.file import FileService

from ui.console import ConsoleUI
from ui.input import ConsoleInput


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

        self.input = ConsoleInput(
            on_play_last=lambda:
                self.ui.play_voice(None)
        )

        self.websocket: ClientConnection | None = None

        self._last_outgoing: tuple[str, str] | None = None

        self.companion = companion

        self._authenticated = asyncio.Event()

        self.crypto = CryptoService()

        self.peer_public_key: (
            X25519PublicKey | None
        ) = None

        self._recording_task: (
            asyncio.Task | None
        ) = None

        http_server_url = (
            self.url
            .replace(
                "ws://",
                "http://",
            )
            .replace(
                "wss://",
                "https://",
            )
            .removesuffix(
                "/ws"
            )
        )

        self.file_service = FileService(
            self.crypto,
            server_url=http_server_url,
        )

    async def connect(self) -> None:

        self.websocket = await websockets.connect(
            self.url
        )

        self.ui.connected()

    async def authenticate(self) -> None:

        packet = AuthRequest(
            payload=AuthPayload(
                token=self.token,
                public_key=(
                    self.crypto.export_public_key()
                ),
            )
        )

        await self.send(packet)

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
            client=self,
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

    def _line_to_packet(
        self,
        line: str,
    ):

        result = parse_line(
            line,
            self.companion,
        )

        if (
            isinstance(result, tuple)
            and result[0] == "switch"
        ):

            self.companion = result[1]

            self.ui.system(
                f"Чат с {self.companion}"
            )

            return GetHistoryRequest(
                payload=GetHistoryPayload(
                    username=self.companion
                )
            )

        return result

    async def _send_media(
        self,
        media_type: str,
        path: Path,
        caption: str,
        to: str,
    ) -> None:

        if self.peer_public_key is None:
            self.ui.error(
                "Public key not received yet."
            )
            return

        if not path.exists():
            self.ui.error(
                f"Файл не существует: {path}"
            )
            return

        try:
            file_size = path.stat().st_size
        except OSError as exc:
            self.ui.error(
                f"Не удалось прочитать файл: {exc}"
            )
            return

        if file_size <= 0:
            self.ui.error(
                "Файл пустой."
            )
            return

        self.ui.info(
            f"Uploading {media_type}..."
        )

        try:
            file_id = (
                await self.file_service.upload_file(
                    path,
                    self.peer_public_key,
                )
            )

        except Exception as exc:
            self.ui.error(
                f"Upload failed: {exc}"
            )
            return

        text = caption

        if caption:
            text = self.crypto.encrypt(
                plaintext=caption,
                peer_public_key=self.peer_public_key,
            )

        packet = SendMessageRequest(
            payload=SendMessagePayload(
                to=to,
                text=text,
                file_id=file_id,
                media_type=media_type,
            )
        )

        display = (
            f"[{media_type}] "
            f"{path.name}"
        )

        if caption:
            display = (
                f"{display}\n"
                f"{caption}"
            )

        self._last_outgoing = (
            to,
            display,
        )

        self.ui.own_message_with_media(
            to=to,
            text=caption or "",
            media_path=path,
            media_type=media_type,
        )

        try:
            await self.send(packet)

        except Exception as exc:
            self.ui.error(
                f"Не удалось отправить сообщение: {exc}"
            )

    async def _toggle_voice(
        self,
        to: str,
    ) -> None:
        """
        Start or stop voice recording.

        Start:
            /voice

        Stop:
            /voice
            or empty Enter while recording.
        """

        vs = self.ui.voice_service

        # ---------------------------------------------------------
        # STOP RECORDING
        # ---------------------------------------------------------

        if vs.is_recording:

            self.ui.info(
                "Останавливаю запись..."
            )

            path = vs.stop_recording()

            self.ui.clear_recording_status()

            if path is None:

                self.ui.error(
                    "Запись слишком короткая "
                    "или FFmpeg не смог создать файл."
                )

                return

            try:
                size = path.stat().st_size
            except OSError:
                size = 0

            if size <= 0:

                self.ui.error(
                    "FFmpeg создал пустой файл."
                )

                path.unlink(
                    missing_ok=True
                )

                return

            duration = (
                vs.duration_seconds(path)
            )

            if duration <= 0:

                self.ui.error(
                    "Не удалось определить "
                    "длительность записи."
                )

                path.unlink(
                    missing_ok=True
                )

                return

            self.ui.info(
                "Запись завершена: "
                f"{vs.format_duration(duration)}"
            )

            await self._send_media(
                "voice",
                path,
                "",
                to,
            )

            return

        # ---------------------------------------------------------
        # START RECORDING
        # ---------------------------------------------------------

        try:

            path = vs.start_recording()

        except Exception as exc:

            self.ui.error(
                f"Не удалось начать запись: {exc}"
            )

            self.ui.info(
                "Проверь микрофон, разрешение "
                "доступа к микрофону Windows "
                "и установку FFmpeg."
            )

            return

        wf = vs.live_waveform(24)

        self.ui.console.print(
            f"[bold red]● REC[/bold red]  "
            f"[yellow]{wf}[/yellow]  "
            f"[dim]/voice или Enter — "
            f"стоп и отправить[/dim]"
        )

        self.ui.info(
            f"Запись: {path.name}"
        )

    async def sender(self) -> None:

        await self._authenticated.wait()

        if self.companion:

            self.ui.reset_group()

            self.ui.system(
                f"Чат с {self.companion}"
            )

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

            recording = (
                self.ui.voice_service.is_recording
            )

            if recording:
                prompt = "● rec > "
            else:
                prompt = (
                    f"{self.companion} > "
                    if self.companion
                    else "you > "
                )

            line = await self.input.read(
                prompt
            )

            print(
                "\033[1A\033[2K",
                end="",
                flush=True,
            )

            # Empty Enter while recording
            # means "stop and send".
            if (
                not line
                and self.ui.voice_service.is_recording
                and self.companion
            ):

                await self._toggle_voice(
                    self.companion
                )

                continue

            if not line:
                continue

            try:

                packet = self._line_to_packet(
                    line
                )

            except CommandError as exc:

                self.ui.error(
                    str(exc)
                )

                continue

            if packet is None:
                continue

            # -----------------------------------------------------
            # HELP
            # -----------------------------------------------------

            if (
                isinstance(packet, tuple)
                and packet[0] == "help"
            ):

                self.ui.help()

                continue

            # -----------------------------------------------------
            # VOICE
            # -----------------------------------------------------

            if (
                isinstance(packet, tuple)
                and packet[0] == "voice"
            ):

                _, to = packet

                await self._toggle_voice(
                    to
                )

                continue

            # -----------------------------------------------------
            # PLAY
            # -----------------------------------------------------

            if (
                isinstance(packet, tuple)
                and packet[0] == "play"
            ):

                _, idx = packet

                ok = self.ui.play_voice(
                    idx
                )

                if not ok:

                    self.ui.error(
                        "Нет голосовых сообщений "
                        "для воспроизведения"
                    )

                else:

                    self.ui.info(
                        "▶ play "
                        f"{idx if idx is not None else 'last'}"
                    )

                continue

            # -----------------------------------------------------
            # MEDIA
            # -----------------------------------------------------

            if (
                isinstance(packet, tuple)
                and packet[0] == "media"
            ):

                (
                    _,
                    media_type,
                    path,
                    caption,
                    to,
                ) = packet

                await self._send_media(
                    media_type,
                    path,
                    caption,
                    to,
                )

                continue

            # -----------------------------------------------------
            # TEXT MESSAGE
            # -----------------------------------------------------

            if isinstance(
                packet,
                SendMessageRequest,
            ):

                if self.peer_public_key is None:

                    self.ui.error(
                        "Public key not received yet."
                    )

                    continue

                plaintext = (
                    packet.payload.text
                )

                ciphertext = (
                    self.crypto.encrypt(
                        plaintext=plaintext,
                        peer_public_key=(
                            self.peer_public_key
                        ),
                    )
                )

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

            name = (
                await self.input.read(
                    "companion >"
                )
            ).strip()

            print(
                "\033[1A\033[2K",
                end="",
                flush=True,
            )

            if not name:
                continue

            if name.startswith("/"):
                self.ui.error(
                    "Введи имя собеседника"
                )
                continue

            self.ui.reset_group()

            self.companion = name

            await self.send(
                PublicKeyRequest(
                    payload=PublicKeyPayload(
                        username=name
                    )
                )
            )

            return

    async def run(self) -> None:

        try:

            import sys

            sys.stdout.write(
                "\x1b[?1000l"
                "\x1b[?1002l"
                "\x1b[?1003l"
                "\x1b[?1006l"
            )

            sys.stdout.flush()

        except Exception:
            pass

        self.ui.banner()

        await self.connect()

        await self.authenticate()

        with patch_stdout(raw=True):

            await asyncio.gather(
                self.receiver(),
                self.sender(),
            )