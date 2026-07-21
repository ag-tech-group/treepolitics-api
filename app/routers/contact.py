import structlog
from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.email import EmailDeliveryError, send_contact_email
from app.schemas.contact import ContactCreate

logger = structlog.get_logger("app.contact")

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def submit_contact(contact: ContactCreate) -> dict[str, str]:
    """Accept a contact-form submission and email it to the site inbox.

    Public endpoint (no auth); rate-limited in main. Honeypot submissions
    are accepted but silently dropped so bots get no signal.
    """
    if contact.website:
        logger.info("contact_honeypot_tripped")
        return {"status": "accepted"}

    if not settings.resend_api_key or not settings.contact_to_email:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Contact form is not configured",
        )

    try:
        await send_contact_email(contact)
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Message could not be sent",
        ) from exc

    return {"status": "accepted"}
