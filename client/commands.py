from protocol import SendMessagePayload, SendMessageRequest


class CommandError(Exception):
    pass


def parse_command(
    command: str,
) -> SendMessageRequest:

    command = command.strip()

    if not command.startswith("/msg "):
        raise CommandError(
            "Unknown command"
        )

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