import os
import time
import threading
from collections import defaultdict, deque
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """
    Lightweight, thread-safe in-memory sliding-window rate limiter.
    Avoids external Redis dependency while protecting auth and AI endpoints.
    """

    def __init__(self):
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> None:
        if os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "false":
            return

        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            q = self._hits[key]
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded ({max_requests} requests per {window_seconds}s). Please wait and retry.",
                    headers={"Retry-After": str(window_seconds)},
                )
            q.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


rate_limiter = SlidingWindowRateLimiter()


def limit_auth_requests(request: Request) -> None:
    limit = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "30"))
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"auth:{client_ip}", max_requests=limit, window_seconds=60)


def limit_ai_requests(request: Request) -> None:
    limit = int(os.getenv("RATE_LIMIT_AI_PER_MIN", "45"))
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"ai:{client_ip}", max_requests=limit, window_seconds=60)
