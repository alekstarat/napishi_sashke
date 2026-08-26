from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    and_,
    or_,
    select,
)
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models import Message, User

from app.protocol.server import (
    ReceiveMessageEvent,
    ReceiveMessagePayload,
)

from app.services.connection import (
    ConnectionService,
)


class MessageService:

    def __init__(
        self,
        connections: ConnectionService,
    ) -> None:

        self._connections = connections

    async def _get_user_by_username(
        self,
        session,
        username: str,
    ) -> User:

        result = await session.execute(
            select(User).where(
                User.username == username
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            raise ValueError(
                f"Unknown user: {username}"
            )

        return user

    async def _create_message(
        self,
        session,
        sender: User,
        recipient: User,
        text: str,
        file_id: str | None = None,
        media_type: str | None = None,
    ) -> Message:

        message = Message(
            uuid=str(uuid4()),

            sender_id=sender.id,

            recipient_id=recipient.id,

            text=text,

            file_id=file_id,

            media_type=media_type,

            timestamp=datetime.now(UTC),

            delivered=False,
        )

        session.add(message)

        await session.commit()

        # Refresh so all DB-generated values are available.
        await session.refresh(message)

        return message

    async def _deliver_message(
        self,
        session,
        message: Message,
        sender: User,
        recipient: User,
    ) -> None:

        # Recipient is offline.
        #
        # Message remains in DB with delivered=False and will
        # be delivered later by the pending-message mechanism.
        if not self._connections.is_online(
            recipient.username
        ):
            return

        payload = ReceiveMessagePayload(
            id=message.uuid,

            sender=sender.username,

            text=message.text,

            timestamp=int(
                message.timestamp.timestamp()
            ),

            # IMPORTANT:
            # These fields were missing before.
            #
            # Without them the receiver gets the message but
            # cannot know which uploaded file belongs to it.
            file_id=message.file_id,

            media_type=message.media_type,
        )

        event = ReceiveMessageEvent(
            payload=payload
        )

        await self._connections.send(
            recipient.username,
            event,
        )

        message.delivered = True

        await session.commit()

    async def send(
        self,
        sender: User,
        recipient: str,
        text: str,
        file_id: str | None = None,
        media_type: str | None = None,
    ) -> Message:

        async with SessionLocal() as session:

            recipient_user = (
                await self._get_user_by_username(
                    session,
                    recipient,
                )
            )

            message = (
                await self._create_message(
                    session=session,
                    sender=sender,
                    recipient=recipient_user,
                    text=text,
                    file_id=file_id,
                    media_type=media_type,
                )
            )

            await self._deliver_message(
                session=session,
                message=message,
                sender=sender,
                recipient=recipient_user,
            )

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

            return result.scalars().all()

    async def get_history(
        self,
        user: User,
        companion_username: str,
    ) -> list[Message]:

        async with SessionLocal() as session:

            companion = (
                await self._get_user_by_username(
                    session,
                    companion_username,
                )
            )

            result = await session.execute(
                select(Message)
                .options(
                    selectinload(
                        Message.sender
                    ),

                    selectinload(
                        Message.recipient
                    ),
                )
                .where(
                    or_(
                        and_(
                            Message.sender_id
                            == user.id,

                            Message.recipient_id
                            == companion.id,
                        ),

                        and_(
                            Message.sender_id
                            == companion.id,

                            Message.recipient_id
                            == user.id,
                        ),
                    )
                )
                .order_by(
                    Message.timestamp
                )
            )

            return result.scalars().all()