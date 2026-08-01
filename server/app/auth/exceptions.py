class AuthenticationError(Exception):
    """Base authentication exception."""


class InvalidToken(AuthenticationError):
    """Invalid authentication token."""


class InvalidPacket(AuthenticationError):
    """Invalid authentication packet."""