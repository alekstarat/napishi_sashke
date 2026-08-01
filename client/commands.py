from dataclasses import dataclass


@dataclass(slots=True)
class SendCommand:
    recipient: str
    text: str


def parse_command(
    command: str,
) -> SendCommand | None:

    command = command.strip()

    if not command.startswith("/msg "):
        return None

    parts = command.split(
        " ",
        2,
    )

    if len(parts) != 3:
        return None

    return SendCommand(
        recipient=parts[1],
        text=parts[2],
    )