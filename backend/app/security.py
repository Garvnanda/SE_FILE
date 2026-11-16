"""Bounded single-process limits for the single Render instance."""

from collections import OrderedDict, deque
from threading import Lock, BoundedSemaphore
import time
from argon2 import PasswordHasher
from fastapi import HTTPException
from starlette.responses import JSONResponse
from .db import settings


class RateLimit:
    def __init__(self, limit, max_keys=10000):
        self.limit, self.max_keys = limit, max_keys
        self.entries = OrderedDict()
        self.lock = Lock()

    def check(self, key):
        with self.lock:
            clock = time.monotonic()
            while self.entries:
                first = next(iter(self.entries))
                if self.entries[first][-1] > clock - 60:
                    break
                self.entries.popitem(last=False)
            q = self.entries.get(key)
            if q is None:
                if len(self.entries) >= self.max_keys:
                    raise HTTPException(429, "Server is busy. Try again in one minute.")
                q = self.entries[key] = deque()
            while q and q[0] <= clock - 60:
                q.popleft()
            if len(q) >= self.limit:
                raise HTTPException(429, "Too many requests. Try again in one minute.")
            q.append(clock)
            self.entries.move_to_end(key)


auth_throttle = RateLimit(30)
write_throttle = RateLimit(120)
_hash_slots = BoundedSemaphore(2)
_hasher = PasswordHasher()


def hash_password(password):
    if not _hash_slots.acquire(blocking=False):
        raise HTTPException(429, "Authentication is busy. Please retry.")
    try:
        return _hasher.hash(password)
    finally:
        _hash_slots.release()


def verify_password(encoded, password):
    if not _hash_slots.acquire(blocking=False):
        raise HTTPException(429, "Authentication is busy. Please retry.")
    try:
        return _hasher.verify(encoded, password)
    finally:
        _hash_slots.release()


class RequestLimits:
    """Reject oversized bodies before parsing; do not trust client forwarding headers."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in ("GET", "HEAD", "OPTIONS"):
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin", b"").decode("latin-1")
        if (
            settings.environment == "production"
            and origin
            and origin != settings.public_origin
        ):
            return await JSONResponse(
                {"error": {"message": "Cross-origin write rejected"}}, 403
            )(scope, receive, send)
        try:
            write_throttle.check((scope.get("client") or ("unknown",))[0])
        except HTTPException as exc:
            return await JSONResponse({"error": {"message": exc.detail}}, 429)(
                scope, receive, send
            )
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            size += len(body)
            if size > 16384:
                return await JSONResponse(
                    {"error": {"message": "Request body exceeds 16 KiB"}}, 413
                )(scope, receive, send)
            chunks.append(body)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {
                    "type": "http.request",
                    "body": b"".join(chunks),
                    "more_body": False,
                }
            return await receive()

        return await self.app(scope, replay, send)
