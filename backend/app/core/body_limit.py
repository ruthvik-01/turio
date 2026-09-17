"""Bound direct API uploads as well as requests passing through the frontend."""

import json

from app.core.context import request_id_var


class BodyTooLarge(Exception):
    pass


class BodyLimitMiddleware:
    def __init__(self, app, max_bytes):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        oversized, sent, received = False, False, 0

        async def reject():
            nonlocal sent
            if sent:
                return
            sent = True
            body = json.dumps({"data": None, "error": {"code": "REQUEST_TOO_LARGE", "message": "Request body exceeds the configured limit."},
                               "request_id": request_id_var.get()}).encode()
            await send({"type": "http.response.start", "status": 413,
                        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
            await send({"type": "http.response.body", "body": body})

        content_length = dict(scope.get("headers", [])).get(b"content-length", b"")
        if content_length.isdigit() and int(content_length) > self.max_bytes:
            return await reject()

        async def limited_receive():
            nonlocal oversized, received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    oversized = True
                    raise BodyTooLarge()
            return message

        async def guarded_send(message):
            if oversized:
                await reject()
            else:
                await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except BodyTooLarge:
            await reject()
