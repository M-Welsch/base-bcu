import logging
from test.utils.patch_config import patch_config
from typing import Generator

import pytest
import yagmail
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

import base.common.mailer
from base.common.logger import LoggerFactory
from base.common.mailer import Mailer


@pytest.fixture
def mailer(mocker: MockFixture) -> Generator[Mailer, None, None]:
    patch_config(Mailer, {"email_notification_receivers": []})
    yield Mailer()


def test_send_summary(mailer: Mailer, mocker: MockFixture) -> None:
    mocked_send = mocker.patch("yagmail.SMTP.send")
    mocked_critial_message_cache = mocker.patch(
        "base.common.logger.LoggerFactory.get_critical_messages", return_value=[]
    )
    mailer.send_summary()
    assert mocked_critial_message_cache.called_once()
    assert mocked_send.called_once()


def test_send_summary_with_error(mailer: Mailer, mocker: MockFixture, caplog: LogCaptureFixture) -> None:
    mocked_send = mocker.patch("yagmail.SMTP.send", side_effect=Exception("one_critical_message"))
    mocked_critial_message_cache = mocker.patch(
        "base.common.logger.LoggerFactory.get_critical_messages", return_value=[]
    )
    with caplog.at_level(logging.CRITICAL):
        mailer.send_summary()
    assert "one_critical_message" in caplog.text
    assert mocked_critial_message_cache.called_once()
    assert mocked_send.called_once()


@pytest.mark.parametrize("critical_messages, backup_ok", [([], True), (["one_critical_message"], False)])
def test_last_backup_ok(mocker: MockFixture, critical_messages: list, backup_ok: bool) -> None:
    mocked_critial_message_cache = mocker.patch(
        "base.common.logger.LoggerFactory.get_critical_messages", return_value=critical_messages
    )
    patch_config(Mailer, {"email_notification_receivers": []})
    mailer = Mailer()
    assert mocked_critial_message_cache.called_once
    assert mailer._last_backup_ok() == backup_ok


@pytest.mark.parametrize("backup_ok", [True, False])
def test_compose_email_subject(mailer: Mailer, mocker: MockFixture, backup_ok: bool) -> None:
    mocked_last_backup_ok = mocker.patch("base.common.mailer.Mailer._last_backup_ok", return_value=backup_ok)
    assert isinstance(mailer._compose_email_subject(), str)
    assert mocked_last_backup_ok.called_once


@pytest.mark.parametrize("backup_ok", [True, False])
def test_compose_email_body(mailer: Mailer, mocker: MockFixture, backup_ok: bool) -> None:
    mocked_last_backup_ok = mocker.patch("base.common.mailer.Mailer._last_backup_ok", return_value=backup_ok)
    assert isinstance(mailer._compose_email_body(), str)
    assert mocked_last_backup_ok.called_once
