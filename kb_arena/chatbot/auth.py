"""Bearer-token auth + rate limiting for LLM-triggering endpoints.

When `KB_ARENA_API_TOKEN` is unset, auth is disabled (localhost dev). When set,
every LLM-triggering endpoint must present `Authorization: Bearer <token>` and
the token is constant-time compared.

Demo mode (`KB_ARENA_DEMO_MODE=true`) returns 503 from any LLM-triggering endpoint
so a hosted public demo cannot drain credits. The static benchmark/leaderboard
pages still work — they read JSON without invoking LLMs.
"""

from __future__ import annotations

import hmac
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

from kb_arena.settings import settings

RATE_LIMIT_RPM = 60
_RATE_LIMIT_MAX_KEYS = 10_000
_rate_store: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=RATE_LIMIT_RPM))


def _client_key(request: Request) -> str:
    """Resolve client identity for rate limiting. Honors trusted proxy header when configured."""
    if settings.trusted_proxy_header:
        forwarded = request.headers.get(settings.trusted_proxy_header)
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request) -> None:
    """Raise 429 if the caller exceeds RATE_LIMIT_RPM. Bounded memory."""
    client_id = _client_key(request)
    now = time.time()
    window = 60.0
    bucket = _rate_store[client_id]
    # Pop entries older than the window
    while bucket and now - bucket[0] >= window:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_RPM:
        raise HTTPException(status_code=429, detail="rate_limited")
    bucket.append(now)
    # Evict cold keys to keep the dict bounded
    if len(_rate_store) > _RATE_LIMIT_MAX_KEYS:
        cold = [k for k, q in _rate_store.items() if not q]
        for k in cold[: len(cold) // 2]:
            _rate_store.pop(k, None)


def require_auth(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    """Bearer-token auth + rate limit + demo-mode gate. Use as `Depends(require_auth)`."""
    if settings.demo_mode:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "demo_mode",
                "message": (
                    "This is a read-only public demo. "
                    "Run KB Arena locally to use chat, arena, tools, and graph endpoints."
                ),
            },
        )

    expected = settings.api_token
    if expected:
        provided = ""
        if authorization and authorization.startswith("Bearer "):
            provided = authorization[len("Bearer ") :].strip()
        if not provided or not hmac.compare_digest(provided, expected):
            raise HTTPException(status_code=401, detail="unauthorized")

    check_rate_limit(request)
