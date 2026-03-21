"""Document delivery — email and SkySlope upload."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


async def send_email(
    to: str | list[str],
    subject: str,
    body: str,
    attachment_path: str | None = None,
) -> bool:
    """Send email with optional PDF attachment via SMTP."""
    settings = get_settings()
    if not settings.is_smtp_configured:
        logger.warning("SMTP not configured — cannot send email")
        return False

    if isinstance(to, str):
        to = [to]

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "pdf")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={Path(attachment_path).name}",
                )
                msg.attach(part)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(msg["From"], to, msg.as_string())

        logger.info("Email sent to %s", to)
        return True

    except Exception as e:
        logger.exception("Failed to send email: %s", e)
        return False


async def upload_to_skyslope(
    file_path: str,
    transaction_id: str,
    doc_type: str = "agreement",
) -> bool:
    """Upload a document to SkySlope transaction management."""
    settings = get_settings()
    if not settings.skyslope_api_key:
        logger.warning("SkySlope not configured")
        return False

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{settings.skyslope_api_url}/v1/transactions/{transaction_id}/documents",
                    headers={"Authorization": f"Bearer {settings.skyslope_api_key}"},
                    files={"file": (Path(file_path).name, f, "application/pdf")},
                    data={"documentType": doc_type},
                )
            if response.status_code in (200, 201):
                logger.info("Uploaded to SkySlope: %s", file_path)
                return True
            else:
                logger.warning("SkySlope upload failed: %s %s", response.status_code, response.text)
                return False

    except Exception as e:
        logger.exception("SkySlope upload error: %s", e)
        return False
