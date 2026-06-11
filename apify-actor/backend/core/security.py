import time
import ipaddress
import re
from collections import defaultdict
from urllib.parse import urlparse

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import get_settings

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::/128"),
]

BLOCKED_HOSTNAMES = {
    "localhost", "0.0.0.0", "127.0.0.1", "::1",
    "metadata.google.internal", "169.254.169.254",
}

ALLOWED_PROTOCOLS = {"http", "https"}
MAX_URL_LENGTH = 2048


def is_internal_url(url: str) -> bool:
    if not url or len(url) > MAX_URL_LENGTH:
        return True
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ALLOWED_PROTOCOLS:
        return True
    hostname = parsed.hostname
    if not hostname:
        return True
    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES:
        return True
    if any(b in hostname_lower for b in BLOCKED_HOSTNAMES):
        return True
    try:
        addr = ipaddress.ip_address(hostname)
        return any(addr in net for net in BLOCKED_IP_RANGES)
    except ValueError:
        return False


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = defaultdict(list)

    def _clean_old(self, key: str, now: float):
        cutoff = now - self.window_seconds
        self._store[key] = [t for t in self._store[key] if t > cutoff]

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        self._clean_old(key, now)
        if len(self._store[key]) >= self.max_requests:
            return True
        self._store[key].append(now)
        return False

    def remaining(self, key: str) -> int:
        now = time.time()
        self._clean_old(key, now)
        return max(0, self.max_requests - len(self._store[key]))


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        settings = get_settings()
        self.limiter = RateLimiter(
            max_requests=settings.api_rate_limit,
            window_seconds=60,
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ("/docs", "/openapi.json", "/redoc", "/health", "/api/v1/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        if self.limiter.is_rate_limited(client_ip):
            retry_after = 60
            return Response(
                content='{"detail":"Too many requests. Please retry in a minute."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(self.limiter.remaining(client_ip))
        response.headers["X-RateLimit-Limit"] = str(self.limiter.max_requests)
        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ("/docs", "/openapi.json", "/redoc", "/health", "/api/v1/health"):
            return await call_next(request)

        api_key = self.settings.api_key
        if not api_key:
            return await call_next(request)

        auth_header = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if not auth_header or auth_header != api_key:
            return Response(
                content='{"detail":"Invalid or missing API Key"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json",
            )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response


class InputSanitizer:
    XSS_PATTERN = re.compile(r'<[^>]*>|javascript:|on\w+\s*=|data:text/html', re.IGNORECASE)
    SQL_PATTERN = re.compile(
        r"(\bSELECT\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\bDROP\b|"
        r"\bUNION\b|\bALTER\b|\bEXEC\b|\bEXECUTE\b|--|;|'|\")",
        re.IGNORECASE,
    )
    MAX_INPUT_LENGTH = 500

    @classmethod
    def sanitize(cls, value: str, max_length: int = 200) -> str:
        if not value:
            return ""
        stripped = value.strip()[:max_length]
        cleaned = cls.XSS_PATTERN.sub("", stripped)
        return cleaned

    @classmethod
    def detect_attack(cls, value: str) -> bool:
        if not value:
            return False
        if cls.XSS_PATTERN.search(value):
            return True
        if len(value) > cls.MAX_INPUT_LENGTH:
            return True
        dangerous = {"../../", "/etc/passwd", "\\x", "%00", "\x00"}
        for d in dangerous:
            if d in value.lower():
                return True
        return False


class AuditLogger:
    def __init__(self):
        self._store: list[dict] = []

    def log(self, event: str, client_ip: str, detail: str = "", query: str = ""):
        masked = query[:30] + "..." if len(query) > 30 else query
        entry = {
            "timestamp": time.time(),
            "event": event,
            "client_ip": client_ip,
            "detail": detail,
            "query_masked": masked,
        }
        self._store.append(entry)
        if len(self._store) > 10000:
            self._store = self._store[-5000:]


audit_logger = AuditLogger()
