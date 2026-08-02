from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from websockets.asyncio.client import ClientConnection
from ui.console import ConsoleUI


T = TypeVar("T")


@dataclass(slots=True)
class PacketContext:
    websocket: ClientConnection
    ui: ConsoleUI
    client: "MessengerClient | None" = None


class PacketHandler(Generic[T], ABC):

    packet_type: type[T]

    @abstractmethod
    async def handle(
        self,
        ctx: PacketContext,
        packet: T,
    ) -> None:
        ...