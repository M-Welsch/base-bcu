from __future__ import annotations

from typing import List

from yagmail import SMTP
from yagmail.error import YagAddressError, YagInvalidEmailAddress

from base.common.config import get_config
from base.common.exceptions import CriticalException
from base.common.logger import LoggerFactory, most_recent_logfile

LOG = LoggerFactory.get_logger(__name__)


class Mailer:
    def __init__(self) -> None:
        self._receivers: List[str] = get_config("base.json").email_notification_receivers

    def send_summary(self) -> None:
        try:
            yag = SMTP("navi.deciv@gmail.com")
            yag.send(
                to=self._receivers,
                subject=self._compose_email_subject(),
                contents=self._compose_email_body(),
                attachments=most_recent_logfile(),
            )
        except (YagAddressError, YagInvalidEmailAddress) as e:
            raise CriticalException from e

    def _last_backup_ok(self) -> bool:
        return True

    def _compose_email_subject(self) -> str:
        if self._last_backup_ok():
            report = "Backup Successful"
        else:
            report = "Error Occured"
        return "Backup Server Email Notification: " + report

    def _compose_email_body(self) -> str:
        return "Lorem Ipsum ..."
