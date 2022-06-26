from __future__ import annotations

import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple

from base.common.config import get_config
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class Mailer:
    def __init__(self) -> None:
        self._config: dict = get_config("notification.json").email
        self._critical_messages = list(LoggerFactory.get_critical_messages())

    def send_summary(self) -> None:
        receivers = self._config["receivers"]
        context = ssl.create_default_context()
        sender_email, password = self._get_credentials()
        message = self._compose_message(sender_email, receivers)
        server = smtplib.SMTP(self._config["smtp_server"], self._config["smtp_port"])
        try:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, password)
            server.sendmail(sender_email, receivers, message.as_string())
        except (
            smtplib.SMTPAuthenticationError,
            smtplib.SMTPServerDisconnected,
            smtplib.SMTPDataError,
            IndexError,
        ) as e:
            LOG.critical(f"Email could not be sent: {e}")
        finally:
            server.quit()

    def _get_credentials(self) -> Tuple[str, str]:
        with open("base/config/.email_credentials", "r") as f:
            lines = f.readlines()
        user = [l for l in lines if "user" in l][0].split("=")[-1].strip()
        password = [l for l in lines if "password" in l][0].split("=")[-1].strip()
        return user, password

    def _compose_message(self, sender: str, receivers: List[str]) -> MIMEMultipart:
        message = MIMEMultipart("mixed")
        message["Subject"] = self._compose_email_subject()
        message["From"] = sender
        message["To"] = ", ".join(receivers)
        message.attach(self._compose_email_body())
        message.attach(self._latest_logfile_attachment())
        return message

    def _last_backup_ok(self) -> bool:
        return not bool(self._critical_messages)

    def _compose_email_subject(self) -> str:
        report = "OK" if self._last_backup_ok() else "Error"
        return "Backup Server Email Notification: " + report

    def _compose_email_body(self) -> MIMEText:
        if self._last_backup_ok():
            body = "No critical errors."
        else:
            critical_messages = "\n".join(list(self._critical_messages))
            body = f"Backup program produced critical errors:\n{critical_messages}"
        return MIMEText(body, "plain")

    def _latest_logfile_attachment(self) -> MIMEBase:
        attachment = MIMEBase("application", "octet-stream")
        current_logfile = LoggerFactory.current_log_file()
        with open(current_logfile, "rb") as f:
            attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename= {current_logfile.stem}.log",
        )
        return attachment
