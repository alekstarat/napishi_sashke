from typing import Annotated, Literal

from pydantic import BaseModel, Field


class AuthResponse(BaseModel):
    type: Literal["auth_ok"] = "auth_ok"

class HistoryMessage(BaseModel):
    id: str
    sender: str
    recipient: str
    text: str
    timestamp: int

class HistoryPayload(BaseModel):
    companion: str
    messages: list[HistoryMessage]

class HistoryResponse(BaseModel):
    type: Literal["history"] = "history"
    payload: HistoryPayload

class SendMessagePayload(BaseModel):
    id: str

class SendMessageResponse(BaseModel):
    type: Literal["send_ok"] = "send_ok"
    payload: SendMessagePayload

class ErrorPayload(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    payload: ErrorPayload


class PongResponse(BaseModel):
    type: Literal["pong"] = "pong"


class ReceiveMessagePayload(BaseModel):
    id: str
    sender: str
    text: str
    timestamp: int


class ReceiveMessageEvent(BaseModel):
    type: Literal["message"] = "message"
    payload: ReceiveMessagePayload


ServerPacket = Annotated[
    AuthResponse
    | ErrorResponse
    | PongResponse
    | ReceiveMessageEvent
    | SendMessageResponse
    | HistoryResponse,
    Field(discriminator="type"),
]