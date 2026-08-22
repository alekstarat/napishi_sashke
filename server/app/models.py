from sqlalchemy import String, Boolean, ForeignKey, Text
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(32),
        unique=True
    )

    token: Mapped[str] = mapped_column(
        String(128),
        unique=True
    )

    public_key = mapped_column(
        Text,
        nullable=True,
    )

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    text: Mapped[str]

    file_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    media_type: Mapped[str | None] = mapped_column(String(16), nullable=True)

    timestamp: Mapped[datetime]

    delivered: Mapped[bool]

    sender: Mapped["User"] = relationship(
        foreign_keys=[sender_id]
    )

    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id]
    )