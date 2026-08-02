from protocol import SendMessagePayload, SendMessageRequest
from protocol.models import GetHistoryRequest, GetHistoryPayload


class CommandError(Exception):
    pass


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

