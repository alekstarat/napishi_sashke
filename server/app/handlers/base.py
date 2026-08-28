from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from fastapi import WebSocket

from app.models import User
from app.services.connection import ConnectionService


T = TypeVar("T")


@dataclass(slots=True)
class PacketContext:
    user: User
    websocket: WebSocket
    connections: ConnectionService
    client_ip: str = "unknown"


class PacketHandler(Generic[T], ABC):

    packet_type: type[T]

    @abstractmethod
    async def handle(
        self,
        ctx: PacketContext,
        packet: T,
    ) -> None:
        raise NotImplementedError
