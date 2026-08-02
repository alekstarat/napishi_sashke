from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.auth.exceptions import AuthenticationError
from app.container import (
    packet_dispatcher,
    websocket_authenticator,
)
from app.database import engine
from app.handlers.base import PacketContext
from app.models import Base
from app.protocol import parser
from app.protocol.client import GetHistoryEvent
from app.protocol.server import HistoryEvent, HistoryPayload, HistoryMessage


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )

    yield


app = FastAPI(
    title="Private Messenger",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "status": "ok"
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):

    await websocket.accept()

    try:
        ctx: PacketContext = await (
            websocket_authenticator.authenticate(
                websocket
            )
        )

    except AuthenticationError:

        await websocket.close(
            code=1008
        )

        return


    try:
        while True:

            raw_packet = await (
                websocket.receive_json()
            )

            packet = parser.parse(
                raw_packet
            )

            await packet_dispatcher.dispatch(
                ctx,
                packet,
            )

    except WebSocketDisconnect:

        pass

    finally:

        ctx.connections.disconnect(
            ctx.user.username
        )