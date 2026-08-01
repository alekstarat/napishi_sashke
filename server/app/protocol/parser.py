from pydantic import TypeAdapter, ValidationError

from .client import ClientPacket


class PacketParser:
    def __init__(self):
        self._adapter = TypeAdapter(ClientPacket)

    def parse(self, data: dict) -> ClientPacket:
        return self._adapter.validate_python(data)


parser = PacketParser()