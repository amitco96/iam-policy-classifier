"""
Request / response logging middleware for IAM Policy Classifier.

Logs one "Request started" line on ingress and one "Request completed"
line on egress for every HTTP request.  GET /health is intentionally
skipped to avoid flooding logs with liveness-probe noise.

Both log records include: request_id, method, path, client_ip.
The egress record also includes: status_code, duration_ms.

The middleware also stamps each response with an X-Request-ID header
so callers can correlate requests with log entries.
"""

import logging
import time
import uuid
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Paths that are excluded from request logging (method-insensitive check
# is kept simple: only GET /health is suppressed).
_HEALTH_PATH = "/health"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every request/response with structured extra fields.

    Skips GET /health to avoid noise from load-balancer probes.
    Always attaches X-Request-ID to the response regardless of whether
    the request is logged.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        skip = request.method == "GET" and request.url.path == _HEALTH_PATH

        client_ip = request.client.host if request.client else "unknown"
        start_time = time.perf_counter()

        if not skip:
            logger.info(
                "Request started",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                },
            )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if not skip:
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

        response.headers["X-Request-ID"] = request_id
        return response
