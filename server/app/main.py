import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.auth.exceptions import AuthenticationError
from app.container import (
    packet_dispatcher,
    security_service,
    websocket_authenticator,
)
from app.database import engine
from app.handlers.base import PacketContext
from app.models import Base
from app.protocol import parser
from app.routers.files import router as files_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("napishi.ws")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Private Messenger",
    lifespan=lifespan,
)

app.include_router(files_router)


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/security/stats")
async def security_stats():
    return security_service.stats()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_ip = security_service.client_ip_from_websocket(websocket)

    allowed, reason = await security_service.check_can_connect(client_ip)
    if not allowed:
        logger.warning("REJECT connect ip=%s reason=%s", client_ip, reason)
        try:
            await websocket.accept()
            await websocket.close(code=1008, reason=reason[:120])
        except Exception:
            pass
        return

    await websocket.accept()
    await security_service.register_connection(client_ip)

    ctx: PacketContext | None = None

    try:
        try:
            ctx = await websocket_authenticator.authenticate(
                websocket,
                client_ip=client_ip,
            )
        except AuthenticationError as exc:
            logger.warning("AUTH fail ip=%s: %s", client_ip, type(exc).__name__)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close(code=1008, reason="authentication failed")
            return

        while True:
            raw_packet = await websocket.receive_json()

            if not await security_service.check_message_rate(client_ip):
                logger.warning("FLOOD drop ip=%s user=%s", client_ip, ctx.user.username)
                continue

            try:
                packet = parser.parse(raw_packet)
            except Exception:
                logger.info("bad packet from %s (%s)", ctx.user.username, client_ip)
                continue

            await packet_dispatcher.dispatch(ctx, packet)

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws error ip=%s", client_ip)
    finally:
        await security_service.unregister_connection(client_ip)
        if ctx is not None:
            ctx.connections.disconnect(ctx.user.username)
