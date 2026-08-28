from app.auth.service import AuthService
from app.auth.websocket import WebSocketAuthenticator

from app.handlers.dispatcher import PacketDispatcher
from app.handlers.get_history import GetHistoryHandler
from app.handlers.ping import PingHandler
from app.handlers.public_key import GetPublicKeyHandler
from app.handlers.send_message import SendMessageHandler

from app.config import settings
from app.services.connection import ConnectionService
from app.services.message import MessageService
from app.services.security import SecurityService, SecuritySettings


_permanent = {
    ip.strip()
    for ip in settings.security_permanent_bans.split(",")
    if ip.strip()
}

security_service = SecurityService(
    SecuritySettings(
        max_failures=settings.security_max_failures,
        failure_window_seconds=settings.security_failure_window_seconds,
        ban_seconds=settings.security_ban_seconds,
        ban_escalate_factor=settings.security_ban_escalate_factor,
        ban_max_seconds=settings.security_ban_max_seconds,
        max_connect_attempts=settings.security_max_connect_attempts,
        connect_window_seconds=settings.security_connect_window_seconds,
        max_concurrent_per_ip=settings.security_max_concurrent_per_ip,
        auth_timeout_seconds=settings.security_auth_timeout_seconds,
        max_messages_per_window=settings.security_max_messages_per_window,
        message_window_seconds=settings.security_message_window_seconds,
        permanent_bans=_permanent,
    )
)

connection_service = ConnectionService()

auth_service = AuthService()

message_service = MessageService(
    connections=connection_service,
)


# Handlers

get_public_key_handler = GetPublicKeyHandler(
    auth_service=auth_service
)

get_history_handler = GetHistoryHandler(
    message_service=message_service
)

ping_handler = PingHandler()

send_message_handler = SendMessageHandler(
    message_service=message_service,
)


# Dispatcher

packet_dispatcher = PacketDispatcher(
    handlers={
        ping_handler.packet_type: ping_handler,
        send_message_handler.packet_type: send_message_handler,
        get_history_handler.packet_type: get_history_handler,
        get_public_key_handler.packet_type: get_public_key_handler
    }
)


# Authentication

websocket_authenticator = WebSocketAuthenticator(
    auth_service=auth_service,
    connections=connection_service,
    security=security_service,
)
