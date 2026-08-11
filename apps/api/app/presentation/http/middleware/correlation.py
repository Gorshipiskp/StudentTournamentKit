"""Request correlation_id / X-Request-ID middleware."""

from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CORRELATION_HEADER = "X-Request-ID"
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return correlation_id_ctx.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get(CORRELATION_HEADER)
        correlation_id = incoming.strip() if incoming and incoming.strip() else str(uuid4())
        token = correlation_id_ctx.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            correlation_id_ctx.reset(token)
        response.headers[CORRELATION_HEADER] = correlation_id
        return response
