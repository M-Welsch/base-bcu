import logging
import sys
from importlib import import_module
from typing import Generator

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.hardware.sbu.commands import SbuCommands
from base.hardware.sbu.communicator import SbuCommunicator
from base.hardware.sbu.sbu import SBU, WakeupReason


@pytest.fixture
def sbu(mocker: MockerFixture) -> Generator[SBU, None, None]:
    mocker.patch("base.hardware.sbu.communicator.SbuCommunicator._get_uart_interface")
    yield SBU(SbuCommunicator())


@pytest.mark.parametrize(
    "wr_code, reason",
    [
        ("WR_BACKUP", WakeupReason.BACKUP_NOW),
        ("WR_CONFIG", WakeupReason.CONFIGURATION),
        ("WR_HB_TIMEOUT", WakeupReason.HEARTBEAT_TIMEOUT),
        ("", WakeupReason.NO_REASON),
    ],
)
def test_request_wakeup_reason(sbu: SBU, mocker: MockerFixture, wr_code: str, reason: WakeupReason) -> None:
    patched_query = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.query", return_value=wr_code)
    assert sbu.request_wakeup_reason() == reason
    patched_query.assert_called_once_with(SbuCommands.request_wakeup_reason)


@pytest.mark.parametrize("wr_code", ["WR_BACKUP", "WR_CONFIG", "WR_HB_TIMEOUT", ""])
def test_set_wakeup_reason(sbu: SBU, mocker: MockerFixture, wr_code: str) -> None:
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    sbu.set_wakeup_reason(wr_code)
    assert patched_write.called_once_with(SbuCommands.set_wakeup_reason, payload=wr_code)


def test_write_to_display(sbu: SBU, mocker: MockerFixture) -> None:
    mocker.patch("base.hardware.sbu.sbu.SBU.check_display_line_for_length")
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    sbu.write_to_display("Line1", "Line2")
    assert patched_write.call_count == 2


@pytest.mark.parametrize("line", ["<16 chars", "excactly 16chars", "more than excactly 16 chars"])
def test_check_display_line_for_length(caplog: LogCaptureFixture, line: str) -> None:
    if len(line) > 16:
        with caplog.at_level(logging.WARNING):
            SBU.check_display_line_for_length(line)
        assert "too long" in caplog.text
    else:
        SBU.check_display_line_for_length(line)


def test_set_display_brightness_percent(sbu: SBU, mocker: MockerFixture) -> None:
    brightness_value = "10"
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    mocker.patch("base.hardware.sbu.sbu.SBU._condition_brightness_value", return_value=brightness_value)
    sbu.set_display_brightness_percent(1)
    assert patched_write.called_once_with(SbuCommands.set_display_brightness, brightness_value)


def test_set_led_brightness_percent(sbu: SBU, mocker: MockerFixture) -> None:
    brightness_value = "10"
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    mocker.patch("base.hardware.sbu.sbu.SBU._condition_brightness_value", return_value=brightness_value)
    sbu.set_led_brightness_percent(1)
    assert patched_write.called_once_with(SbuCommands.set_led_brightness, brightness_value)


@pytest.mark.parametrize("input_value, output_value", [(-1, 0), (0, 0), (50, 32767), (101, 65535)])
def test_condition_brightness_value(input_value: float, output_value: int, caplog: LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        assert output_value == SBU._condition_brightness_value(input_value)
    if input_value < 0:
        assert "shall not be negative" in caplog.text
    if input_value > 100:
        assert "clipping" in caplog.text and "to maximum" in caplog.text


def test_send_seconds_to_next_bu(sbu: SBU, mocker: MockerFixture) -> None:
    input_seconds = 10
    patched_query = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.query", return_value=10)
    mocker.patch("base.hardware.sbu.sbu.SBU._assert_correct_rtc_setting")
    sbu.send_seconds_to_next_bu(input_seconds)
    assert patched_query.called_once_with(SbuCommands.set_seconds_to_next_bu, str(input_seconds))


def test_assert_correct_rtc_setting() -> None:
    ...
