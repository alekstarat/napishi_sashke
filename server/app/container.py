from app.auth.service import AuthService
from app.auth.websocket import WebSocketAuthenticator

from app.handlers.dispatcher import PacketDispatcher
from app.handlers.get_history import GetHistoryHandler
from app.handlers.ping import PingHandler
from app.handlers.send_message import SendMessageHandler

from app.services.connection import ConnectionService
from app.services.message import MessageService


# Core services

connection_service = ConnectionService()

auth_service = AuthService()

message_service = MessageService(
    connections=connection_service,
)

get_history_handler = GetHistoryHandler(
    message_service=message_service
)
# Handlers

ping_handler = PingHandler()

send_message_handler = SendMessageHandler(
    message_service=message_service,
)


# Dispatcher

packet_dispatcher = PacketDispatcher(
    handlers={
        ping_handler.packet_type: ping_handler,
        send_message_handler.packet_type: send_message_handler,
        get_history_handler.packet_type: get_history_handler
    }
)


# Authentication

websocket_authenticator = WebSocketAuthenticator(
    auth_service=auth_service,
    connections=connection_service,
)