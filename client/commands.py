from pathlib import Path

from protocol import SendMessagePayload, SendMessageRequest
from protocol.models import GetHistoryRequest, GetHistoryPayload


class CommandError(Exception):
    pass


def parse_line(line: str, companion: str | None):
    line = line.strip()
    if not line:
        return None

    if line == "/quit":
        raise SystemExit

    if line == "/help":
        return ("help",)

    if line.startswith("/chat "):
        name = line.split(maxsplit=1)[1].strip()
        if not name:
            raise CommandError("Usage: /chat <user>")
        return ("switch", name)

    # /voice — start or stop recording
    if line == "/voice" or line.startswith("/voice "):
        if not companion:
            raise CommandError("Сначала выбери собеседника")
        return ("voice", companion)

    # /play [n]
    if line == "/play" or line.startswith("/play "):
        parts = line.split()
        idx = None
        if len(parts) >= 2:
            try:
                idx = int(parts[1])
            except ValueError:
                raise CommandError("Usage: /play [номер]")
        return ("play", idx)

    for media in ("photo", "audio"):
        prefix = f"/{media} "
        if line.startswith(prefix):
            rest = line[len(prefix):].strip()
            if not rest:
                raise CommandError(f"Usage: /{media} <path> [caption]")
            parts = rest.split(maxsplit=1)
            path = Path(parts[0]).expanduser()
            caption = parts[1] if len(parts) > 1 else ""
            if not path.is_file():
                raise CommandError(f"File not found: {path}")
            if not companion:
                raise CommandError("Сначала выбери собеседника")
            return ("media", media, path, caption, companion)

    if line.startswith("/"):
        raise CommandError("Unknown command")

    if not companion:
        raise CommandError("Сначала выбери собеседника")

    return SendMessageRequest(
        payload=SendMessagePayload(to=companion, text=line)
    )


def parse_command(
    command: str,
):

    command = command.strip()

    if command.startswith("/msg "):
        parts = command.split(
            " ",
            2,
        )

        if len(parts) != 3:
            raise CommandError(
                "Usage: /msg <user> <text>"
            )

        return SendMessageRequest(
            payload=SendMessagePayload(
                to=parts[1],
                text=parts[2],
            )
        )

    elif command.startswith("/history "):
        parts = command.split(maxsplit=1)
        if len(parts) != 2:
            raise CommandError("Usage: /history <user>")


        return GetHistoryRequest(
            payload=GetHistoryPayload(username=parts[1])
        )

    else:
        raise CommandError(
            Exception("Unknown command")
        )
