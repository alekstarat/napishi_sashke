from typing import Annotated, Literal

from pydantic import BaseModel, Field


class AuthPayload(BaseModel):
    token: str
    public_key: str


class AuthRequest(BaseModel):
    type: Literal["auth"] = "auth"
    payload: AuthPayload

class GetPublicKeyPayload(BaseModel):
    username: str

class GetPublicKeyRequest(BaseModel):
    type: Literal["get_public_key"] = "get_public_key"
    payload: GetPublicKeyPayload


class SendMessagePayload(BaseModel):
    to: str
    text: str = ""
    file_id: str | None = None
    media_type: str | None = None


class SendMessageRequest(BaseModel):
    type: Literal["send"] = "send"
    payload: SendMessagePayload


class PingRequest(BaseModel):
    type: Literal["ping"] = "ping"
    payload: dict = {}

class GetHistoryPayload(BaseModel):
    username: str

class GetHistoryRequest(BaseModel):
    type: Literal["get_history"] = "get_history"
    payload: GetHistoryPayload


ClientPacket = Annotated[
    AuthRequest | SendMessageRequest | PingRequest | GetHistoryRequest | GetPublicKeyRequest,
    Field(discriminator="type"),
]