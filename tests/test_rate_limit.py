"""Rate limits must apply per caller behind Cloud Run's proxy.

Cloud Run connects to the container from a link-local address and passes the caller's IP
in X-Forwarded-For. start.sh has uvicorn trust that header only from link-local peers;
these tests wrap the app in uvicorn's ProxyHeadersMiddleware with that same setting.
"""

import re
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import app.main as main_module
from app.auth.security_logging import SecurityEvent
from app.main import app

# Read the trusted-proxy default from start.sh so the tests follow the real entrypoint
_START_SH = (Path(__file__).parent.parent / "start.sh").read_text()
TRUSTED_PROXIES = re.search(r"FORWARDED_ALLOW_IPS:-([^}]+)}", _START_SH).group(1)

CLOUD_RUN_PROXY = ("169.254.169.126", 40000)  # the peer address Cloud Run connects from
LOGIN_LIMIT = 5  # /auth/jwt/login allows 5 attempts per minute
BAD_LOGIN = {"username": "nobody@example.com", "password": "wrong-password"}


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    app.state.limiter._limiter.storage.reset()
    yield
    app.state.limiter._limiter.storage.reset()


def client_from(peer: tuple[str, int]) -> AsyncClient:
    """Client whose requests reach the app from `peer`, as uvicorn serves it in production."""
    proxied = ProxyHeadersMiddleware(app, trusted_hosts=TRUSTED_PROXIES)
    return AsyncClient(transport=ASGITransport(app=proxied, client=peer), base_url="http://test")


async def attempt_login(client: AsyncClient, forwarded_for: str) -> int:
    response = await client.post(
        "/auth/jwt/login", data=BAD_LOGIN, headers={"X-Forwarded-For": forwarded_for}
    )
    return response.status_code


async def test_callers_behind_proxy_get_separate_limits(monkeypatch: pytest.MonkeyPatch):
    events: list[tuple[SecurityEvent, str]] = []

    def record(event: SecurityEvent, *, request, **kwargs) -> None:
        events.append((event, request.client.host))

    monkeypatch.setattr(main_module, "log_security_event", record)

    async with client_from(CLOUD_RUN_PROXY) as client:
        for _ in range(LOGIN_LIMIT):
            assert await attempt_login(client, "203.0.113.10") == 400
        assert await attempt_login(client, "203.0.113.10") == 429

        # Another caller through the same proxy still has its full allowance
        assert await attempt_login(client, "198.51.100.20") == 400

    # The security log names the real caller, not the proxy
    assert events == [(SecurityEvent.RATE_LIMIT_HIT, "203.0.113.10")]


async def test_spoofed_forwarded_for_cannot_dodge_limit():
    # Callers can prepend anything to X-Forwarded-For; only the entry Cloud Run appends counts
    async with client_from(CLOUD_RUN_PROXY) as client:
        statuses = [
            await attempt_login(client, f"10.0.0.{i}, 203.0.113.10") for i in range(LOGIN_LIMIT + 1)
        ]

    assert statuses[-1] == 429


async def test_forwarded_for_ignored_from_untrusted_peer():
    # A caller that isn't Cloud Run's proxy can't choose its identity via the header
    async with client_from(("203.0.113.99", 40000)) as client:
        statuses = [await attempt_login(client, f"198.51.100.{i}") for i in range(LOGIN_LIMIT + 1)]

    assert statuses[-1] == 429
