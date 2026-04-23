from __future__ import annotations

import asyncio
import logging
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ReminderResult:
    participant_id: str
    success: bool
    error: str | None = None


class ReminderService:
    def _build_email(
        self,
        recipient: str,
        name: str | None,
        invite_url: str,
        custom_message: str,
    ) -> MIMEMultipart:
        display_name = name or "Participant"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reminder: Your survey is waiting for you"
        msg["From"] = settings.from_email
        msg["To"] = recipient

        text_body = (
            f"Hello {display_name},\n\n"
            f"{custom_message}\n\n"
            f"Complete your survey here: {invite_url}\n\n"
            "Thank you,\nThe Voxora Team"
        )
        html_body = (
            f"<html><body>"
            f"<p>Hello {display_name},</p>"
            f"<p>{custom_message}</p>"
            f'<p><a href="{invite_url}">Click here to complete your survey</a></p>'
            f"<p>Thank you,<br>The Voxora Team</p>"
            f"</body></html>"
        )

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        return msg

    async def send_reminder(
        self,
        email: str,
        name: str | None,
        invite_url: str,
        custom_message: str,
        participant_id: str,
    ) -> ReminderResult:
        try:
            msg = self._build_email(email, name, invite_url, custom_message)
            # Run blocking SMTP in executor to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._send_smtp, settings.from_email, email, msg.as_string()
            )
            return ReminderResult(participant_id=participant_id, success=True)
        except Exception as exc:
            logger.error("Failed to send reminder to %s: %s", email, exc)
            return ReminderResult(
                participant_id=participant_id, success=False, error=str(exc)
            )

    def _send_smtp(self, from_addr: str, to_addr: str, message: str) -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(from_addr, to_addr, message)


reminder_service = ReminderService()
