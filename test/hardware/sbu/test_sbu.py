import logging
import sys
from importlib import import_module
from typing import Generator

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.hardware.sbu.commands import SbuCommands
from base.hardware.sbu.communicator import SbuCommunicator
from base.hardware.sbu.sbu import SBU, WakeupReason


@pytest.fixture
def sbu(mocker: MockFixture) -> Generator[SBU, None, None]:
    mocker.patch("base.hardware.sbu.communicator.SbuCommunicator._get_uart_interface")
    yield SBU()


@pytest.mark.parametrize(
    "wr_code, reason",
    [
        ("WR_BACKUP", WakeupReason.BACKUP_NOW),
        ("WR_CONFIG", WakeupReason.CONFIGURATION),
        ("WR_HB_TIMEOUT", WakeupReason.HEARTBEAT_TIMEOUT),
        ("", WakeupReason.NO_REASON),
    ],
)
def test_request_wakeup_reason(sbu: SBU, mocker: MockFixture, wr_code: str, reason: WakeupReason) -> None:
    mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.query", return_value=wr_code)
    assert sbu.request_wakeup_reason() == reason
    assert sbu._sbu_communicator.query.call_count == 1  # type: ignore
    # assert sbu_instance._sbu_communicator.query.assert_called_once_with(SbuCommands.request_wakeup_reason.message_code, "")  # Fixme: why does this not work


@pytest.mark.parametrize("wr_code", ["WR_BACKUP", "WR_CONFIG", "WR_HB_TIMEOUT", ""])
def test_set_wakeup_reason(sbu: SBU, mocker: MockFixture, wr_code: str) -> None:
    mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    sbu.set_wakeup_reason(wr_code)
    # sbu._sbu_communicator.write.assert_called_once_with(wr_code)  # Fixme: why does this not work
    assert sbu._sbu_communicator.write.call_count == 1  # type: ignore


def test_write_to_display(sbu: SBU, mocker: MockFixture) -> None:
    mocker.patch("base.hardware.sbu.sbu.SBU.check_display_line_for_length")
    mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    sbu.write_to_display("Line1", "Line2")
    assert sbu._sbu_communicator.write.call_count == 2  # type: ignore


@pytest.mark.parametrize("line", ["<16 chars", "excactly 16chars", "more than excactly 16 chars"])
def test_check_display_line_for_length(caplog: LogCaptureFixture, line: str) -> None:
    if len(line) > 16:
        with caplog.at_level(logging.WARNING):
            SBU.check_display_line_for_length(line)
        assert "too long" in caplog.text
    else:
        SBU.check_display_line_for_length(line)
