from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque

from fastapi import Request, WebSocket

logger = logging.getLogger("napishi.security")


@dataclass
class SecuritySettings:
    max_failures: int = 5
    failure_window_seconds: float = 300.0  # 5 min

    ban_seconds: float = 900.0  # 15 min

    ban_escalate_factor: float = 2.0
    ban_max_seconds: float = 86400.0  # 24 h

    max_connect_attempts: int = 20
    connect_window_seconds: float = 60.0

    max_concurrent_per_ip: int = 3

    auth_timeout_seconds: float = 8.0

    max_messages_per_window: int = 60
    message_window_seconds: float = 10.0

    permanent_bans: set[str] = field(default_factory=set)


@dataclass
class _IpState:
    failures: Deque[float] = field(default_factory=deque)
    connect_attempts: Deque[float] = field(default_factory=deque)
    message_times: Deque[float] = field(default_factory=deque)
    ban_until: float = 0.0
    ban_count: int = 0
    concurrent: int = 0


class SecurityService:
    def __init__(self, settings: SecuritySettings | None = None) -> None:
        self.settings = settings or SecuritySettings()
        self._ips: dict[str, _IpState] = defaultdict(_IpState)
        self._lock = asyncio.Lock()

    # ── IP extraction ──────────────────────────────────────────────

    @staticmethod
    def client_ip_from_websocket(websocket: WebSocket) -> str:
        """Prefer X-Forwarded-For / X-Real-IP when behind a reverse proxy"""
        headers = websocket.headers
        forwarded = headers.get("x-forwarded-for") or headers.get("x-real-ip")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if websocket.client:
            return websocket.client.host or "unknown"
        return "unknown"

    @staticmethod
    def client_ip_from_request(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host or "unknown"
        return "unknown"

    # ── Ban / rate checks ──────────────────────────────────────────

    def _purge_old(self, dq: Deque[float], window: float, now: float) -> None:
        while dq and (now - dq[0]) > window:
            dq.popleft()

    def is_banned(self, ip: str) -> bool:
        if ip in self.settings.permanent_bans:
            return True
        state = self._ips[ip]
        return time.monotonic() < state.ban_until

    def ban_remaining(self, ip: str) -> float:
        if ip in self.settings.permanent_bans:
            return float("inf")
        state = self._ips[ip]
        return max(0.0, state.ban_until - time.monotonic())

    async def check_can_connect(self, ip: str) -> tuple[bool, str]:
        async with self._lock:
            now = time.monotonic()
            s = self.settings
            state = self._ips[ip]

            if ip in s.permanent_bans:
                return False, "permanent ban"

            if now < state.ban_until:
                remaining = int(state.ban_until - now)
                return False, f"banned for {remaining}s"

            self._purge_old(state.connect_attempts, s.connect_window_seconds, now)
            if len(state.connect_attempts) >= s.max_connect_attempts:
                self._apply_ban(ip, state, now, reason="connect flood")
                return False, "too many connection attempts"

            if state.concurrent >= s.max_concurrent_per_ip:
                return False, "too many concurrent connections from this IP"

            state.connect_attempts.append(now)
            return True, ""

    async def register_connection(self, ip: str) -> None:
        async with self._lock:
            self._ips[ip].concurrent += 1

    async def unregister_connection(self, ip: str) -> None:
        async with self._lock:
            state = self._ips[ip]
            state.concurrent = max(0, state.concurrent - 1)

    def _apply_ban(self, ip: str, state: _IpState, now: float, reason: str) -> None:
        state.ban_count += 1
        duration = min(
            self.settings.ban_seconds * (self.settings.ban_escalate_factor ** (state.ban_count - 1)),
            self.settings.ban_max_seconds,
        )
        state.ban_until = now + duration
        state.failures.clear()
        logger.warning(
            "BAN ip=%s duration=%.0fs reason=%s ban_count=%d",
            ip,
            duration,
            reason,
            state.ban_count,
        )

    async def report_failure(self, ip: str, reason: str = "auth failure") -> None:
        async with self._lock:
            now = time.monotonic()
            s = self.settings
            state = self._ips[ip]
            self._purge_old(state.failures, s.failure_window_seconds, now)
            state.failures.append(now)
            logger.info("FAILURE ip=%s reason=%s count=%d", ip, reason, len(state.failures))
            if len(state.failures) >= s.max_failures:
                self._apply_ban(ip, state, now, reason=reason)

    async def check_message_rate(self, ip: str) -> bool:
        async with self._lock:
            now = time.monotonic()
            s = self.settings
            state = self._ips[ip]
            self._purge_old(state.message_times, s.message_window_seconds, now)
            if len(state.message_times) >= s.max_messages_per_window:
                return False
            state.message_times.append(now)
            return True

    def stats(self) -> dict:
        now = time.monotonic()
        banned = {
            ip: round(st.ban_until - now, 1)
            for ip, st in self._ips.items()
            if now < st.ban_until or ip in self.settings.permanent_bans
        }
        return {
            "tracked_ips": len(self._ips),
            "currently_banned": banned,
        }

security_service = SecurityService()
