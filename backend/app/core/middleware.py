from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.context import correlation_id_var


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    header = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        correlation_id = request.headers.get(self.header) or str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
        request.state.correlation_id = correlation_id

        started = time.perf_counter()
        response: Response = await call_next(request)
        response.headers[self.header] = correlation_id
        response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.1f}"
        return response
