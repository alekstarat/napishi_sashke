from typing import Annotated, Literal

from pydantic import BaseModel, Field


class AuthResponse(BaseModel):
    type: Literal["auth_ok"] = "auth_ok"

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
    | SendMessageResponse,
    Field(discriminator="type"),
]