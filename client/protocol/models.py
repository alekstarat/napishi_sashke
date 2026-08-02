from typing import Literal

from pydantic import BaseModel, Field


# =====================
# Auth
# =====================

class AuthPayload(BaseModel):
    token: str


class AuthRequest(BaseModel):
    type: Literal["auth"] = "auth"
    payload: AuthPayload


class AuthResponse(BaseModel):
    type: Literal["auth_ok"] = "auth_ok"


# =====================
# Message sending
# =====================

class SendMessagePayload(BaseModel):
    to: str
    text: str


class SendMessageRequest(BaseModel):
    type: Literal["send"] = "send"
    payload: SendMessagePayload


class SendMessageResponsePayload(BaseModel):
    id: str


class SendMessageResponse(BaseModel):
    type: Literal["send_ok"] = "send_ok"
    payload: SendMessageResponsePayload


# =====================
# Incoming messages
# =====================

class ReceiveMessagePayload(BaseModel):
    id: str
    sender: str
    text: str
    timestamp: int


class ReceiveMessageEvent(BaseModel):
    type: Literal["message"] = "message"
    payload: ReceiveMessagePayload

# =====================
# History
# =====================

class GetHistoryPayload(BaseModel):
    username: str

class GetHistoryRequest(BaseModel):
    type: Literal["get_history"] = "get_history"
    payload: GetHistoryPayload

class HistoryMessage(BaseModel):
    id: str
    sender: str
    recipient: str
    text: str
    timestamp: int

class HistoryPayload(BaseModel):
    companion: str          # с кем диалог
    messages: list[HistoryMessage]

class HistoryResponse(BaseModel):
    type: Literal["history"] = "history"
    payload: HistoryPayload

# =====================
# Errors
# =====================

class ErrorPayload(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    payload: ErrorPayload


# =====================
# Ping
# =====================

class PongResponse(BaseModel):
    type: Literal["pong"] = "pong"