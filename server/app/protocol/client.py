from typing import Annotated, Literal

from pydantic import BaseModel, Field


class AuthPayload(BaseModel):
    token: str


class AuthRequest(BaseModel):
    type: Literal["auth"] = "auth"
    payload: AuthPayload


class SendMessagePayload(BaseModel):
    to: str
    text: str


class SendMessageRequest(BaseModel):
    type: Literal["send"] = "send"
    payload: SendMessagePayload


class PingRequest(BaseModel):
    type: Literal["ping"] = "ping"
    payload: dict = {}

class GetHistoryPayload(BaseModel):
    username: str

class GetHistoryEvent(BaseModel):
    event: str = "get_history"
    payload: GetHistoryPayload


ClientPacket = Annotated[
    AuthRequest | SendMessageRequest | PingRequest,
    Field(discriminator="type"),
]