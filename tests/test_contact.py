import pytest
from httpx import AsyncClient

import app.routers.contact as contact_module
from app.config import settings
from app.email import EmailDeliveryError
from app.main import app

VALID_PAYLOAD = {
    "name": "A Reader",
    "email": "reader@example.com",
    "subject": "About the cherry trees post",
    "message": "I have a question about the sources in that post.",
}


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """/contact is rate-limited at 3/minute; reset the in-memory window per test."""
    app.state.limiter._limiter.storage.reset()
    yield
    app.state.limiter._limiter.storage.reset()


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "resend_api_key", "test-key")
    monkeypatch.setattr(settings, "contact_to_email", "inbox@example.com")


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list:
    """Replace the Resend call; record payloads instead of sending."""
    calls: list = []

    async def fake_send(contact) -> None:
        calls.append(contact)

    monkeypatch.setattr(contact_module, "send_contact_email", fake_send)
    return calls


async def test_submit_sends_email(client: AsyncClient, configured, sent: list):
    response = await client.post("/contact", json=VALID_PAYLOAD)

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
    assert len(sent) == 1
    assert sent[0].email == "reader@example.com"
    assert sent[0].subject == VALID_PAYLOAD["subject"]


async def test_honeypot_accepted_but_not_sent(client: AsyncClient, configured, sent: list):
    response = await client.post("/contact", json={**VALID_PAYLOAD, "website": "spam.example"})

    assert response.status_code == 202
    assert sent == []


async def test_unconfigured_returns_503(client: AsyncClient, sent: list):
    response = await client.post("/contact", json=VALID_PAYLOAD)

    assert response.status_code == 503
    assert sent == []


async def test_delivery_failure_returns_502(
    client: AsyncClient, configured, monkeypatch: pytest.MonkeyPatch
):
    async def failing_send(contact) -> None:
        raise EmailDeliveryError("provider down")

    monkeypatch.setattr(contact_module, "send_contact_email", failing_send)

    response = await client.post("/contact", json=VALID_PAYLOAD)

    assert response.status_code == 502


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"name": ""},
        {"message": "short"},
        {"subject": ""},
    ],
)
async def test_invalid_payload_returns_422(
    client: AsyncClient, configured, sent: list, overrides: dict
):
    response = await client.post("/contact", json={**VALID_PAYLOAD, **overrides})

    assert response.status_code == 422
    assert sent == []


async def test_rate_limited_after_three_requests(client: AsyncClient, configured, sent: list):
    for _ in range(3):
        response = await client.post("/contact", json=VALID_PAYLOAD)
        assert response.status_code == 202

    response = await client.post("/contact", json=VALID_PAYLOAD)

    assert response.status_code == 429
    assert len(sent) == 3
