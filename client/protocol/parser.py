from pydantic import ValidationError

from protocol import (
    AuthResponse,
    ErrorResponse,
    ReceiveMessageEvent,
    SendMessageResponse,
    PongResponse,
    HistoryResponse
)

PACKET_TYPES = (
    AuthResponse,
    ErrorResponse,
    ReceiveMessageEvent,
    SendMessageResponse,
    PongResponse,
    HistoryResponse
)


class UnknownPacket(Exception):
    pass


def parse_packet(
    data: dict,
):
    packet_type = data.get(
        "type"
    )

    if packet_type is None:
        raise UnknownPacket(
            "Packet has no type"
        )


    for packet_model in PACKET_TYPES:

        try:
            packet = packet_model.model_validate(
                data
            )

            return packet

        except ValidationError:
            continue


    raise UnknownPacket(
        f"Unknown packet type: {packet_type}"
    )