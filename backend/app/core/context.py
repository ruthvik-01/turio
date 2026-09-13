"""Request-scoped context shared by middleware, logging and error handling.

The request id is set once per request by `RequestIdMiddleware` and read by the
JSON log formatter and the error handlers, so a log line and an error envelope
for the same request always agree.
"""

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
