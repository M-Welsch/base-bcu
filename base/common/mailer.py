from __future__ import annotations

from typing import List

from yagmail import SMTP
from yagmail.error import YagAddressError, YagInvalidEmailAddress

from base.common.config import get_config
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class Mailer:
    def __init__(self) -> None:
        self._receivers: List[str] = get_config("base.json").email_notification_receivers
        self._critical_messages = LoggerFactory.get_critical_messages()

    def send_summary(self) -> None:
        try:
            yag = SMTP("navi.deciv@gmail.com")
            yag.send(
                to=self._receivers,
                subject=self._compose_email_subject(),
                contents=self._compose_email_body(),
                attachments=LoggerFactory.current_log_file(),
            )
        except Exception as e:
            LOG.critical(f"Error occurent during sending summary: {e}")

    def _last_backup_ok(self) -> bool:
        return not bool(self._critical_messages)

    def _compose_email_subject(self) -> str:
            report = "Backup Successful" if self._last_backup_ok() else "Error Occured"
        return "Backup Server Email Notification: " + report

    def _compose_email_body(self) -> str:
        if self._last_backup_ok():
            body = "Backup conducted successfully!"
        else:
            critical_messages = "\n".join(list(self._critical_messages))
            body = f"""Backup program produced critical errors:
{critical_messages}
"""
        return body
