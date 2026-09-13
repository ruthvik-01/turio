"""Structured JSON logging.

DEPLOYMENT.md section 5 requires structured logs carrying a request id, so
every record is emitted as a single JSON object rather than a formatted
sentence. Per-record context is passed via `extra={"extra_fields": {...}}`.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.context import request_id_var

_configured = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        payload.update(getattr(record, "extra_fields", None) or {})
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    """Install the JSON formatter once.

    Idempotent, and deliberately non-destructive: handlers already on the root
    logger (pytest's capture handler, for instance) are left in place.
    """
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    _configured = True
