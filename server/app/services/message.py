from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Message, User
from app.protocol.server import (
    ReceiveMessageEvent,
    ReceiveMessagePayload,
)
from app.services.connection import ConnectionService


class MessageService:
    def __init__(
        self,
        connections: ConnectionService,
    ) -> None:
        self._connections = connections

    async def send(
        self,
        sender: User,
        recipient: str,
        text: str,
    ) -> Message:
        async with SessionLocal() as session:

            result = await session.execute(
                select(User).where(
                    User.username == recipient
                )
            )

            recipient_user = result.scalar_one_or_none()

            if recipient_user is None:
                raise ValueError(
                    f"Unknown user: {recipient}"
                )

            message = Message(
                uuid=str(uuid4()),
                sender_id=sender.id,
                recipient_id=recipient_user.id,
                text=text,
                timestamp=datetime.now(UTC),
                delivered=False,
            )

            session.add(message)
            await session.commit()

            if self._connections.is_online(recipient):
                await self._connections.send(
                    recipient,
                    ReceiveMessageEvent(
                        payload=ReceiveMessagePayload(
                            id=message.uuid,
                            sender=sender.username,
                            text=message.text,
                            timestamp=int(
                                message.timestamp.timestamp()
                            ),
                        )
                    ),
                )

                message.delivered = True

                await session.commit()

                return message

    async def get_pending(
            self,
            user_id: int,
    ) -> list[Message]:

        async with SessionLocal() as session:
            result = await session.execute(
                select(Message)
                .where(
                    Message.recipient_id == user_id,
                    Message.delivered == False,
                )
                .order_by(
                    Message.timestamp
                )
            )

            messages = result.scalars().all()

            return messages