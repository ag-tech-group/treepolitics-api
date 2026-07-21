"""Outbound email via the Resend HTTP API."""

import httpx
import structlog

from app.config import settings
from app.schemas.contact import ContactCreate

logger = structlog.get_logger("app.email")

RESEND_API_URL = "https://api.resend.com/emails"


class EmailDeliveryError(Exception):
    """Raised when the email provider rejects or fails a send."""


async def send_contact_email(contact: ContactCreate) -> None:
    """Deliver a contact-form submission to the site inbox.

    The submitter's address goes in Reply-To so replying from the inbox
    reaches them directly; From stays on the verified sending domain.
    """
    body = (
        f"From: {contact.name} <{contact.email}>\nSubject: {contact.subject}\n\n{contact.message}\n"
    )
    payload = {
        "from": settings.contact_from_email,
        "to": [settings.contact_to_email],
        "reply_to": [contact.email],
        "subject": f"[Contact] {contact.subject}",
        "text": body,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                RESEND_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            )
    except httpx.HTTPError as exc:
        logger.error("contact_email_transport_error", error=str(exc))
        raise EmailDeliveryError("email provider unreachable") from exc

    if response.status_code >= 400:
        logger.error(
            "contact_email_rejected",
            status_code=response.status_code,
            body=response.text[:500],
        )
        raise EmailDeliveryError(f"email provider returned {response.status_code}")
