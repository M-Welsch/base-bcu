import logging
import sys
from importlib import import_module
from typing import Callable, Generator

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

# from base.hardware.platform import has_sbu
from base.hardware.sbu.commands import SbuCommand, SbuCommands
from base.hardware.sbu.communicator import SbuCommunicator
from base.hardware.sbu.sbu import SBU, WakeupReason


@pytest.fixture
def sbu(mocker: MockerFixture) -> Generator[SBU, None, None]:
    mocker.patch("base.hardware.platform.has_sbu", return_value=True)
    mocker.patch("base.hardware.sbu.communicator.SbuCommunicator._get_uart_interface")
    sbu = SBU(SbuCommunicator())
    yield sbu


@pytest.mark.skip(reason="mocking doesnt work properly yet")
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
    sbu._sbu_communicator.query = sbu._sbu_communicator._query_production  # type: ignore
    assert sbu.request_wakeup_reason() == reason
    assert patched_query.called_once_with(SbuCommands.request_wakeup_reason)


@pytest.mark.parametrize("wr_code", ["WR_BACKUP", "WR_CONFIG", "WR_HB_TIMEOUT", ""])
def test_set_wakeup_reason(sbu: SBU, mocker: MockerFixture, wr_code: str) -> None:
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    sbu.set_wakeup_reason(wr_code)
    assert patched_write.called_once_with(SbuCommands.set_wakeup_reason, payload=wr_code)


@pytest.mark.skip(reason="mocking doesnt work properly yet")
def test_write_to_display(sbu: SBU, mocker: MockerFixture) -> None:
    mocker.patch("base.hardware.sbu.sbu.SBU.check_display_line_for_length")
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.__write_mock")
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


@pytest.mark.parametrize("rtc_register, secs, error_log", [("1", 32, False), ("2", 32, True)])
def test_assert_correct_rtc_setting(rtc_register: str, secs: int, error_log: bool, caplog: LogCaptureFixture) -> None:
    if error_log:
        with caplog.at_level(logging.ERROR):
            SBU._assert_correct_rtc_setting(rtc_register, secs)
        assert "didn't calculate the time to next backup correctly" in caplog.text


def test_send_readable_timestamp(sbu: SBU, mocker: MockerFixture) -> None:
    timestamp = "SomeString"
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    sbu.send_readable_timestamp(timestamp)
    assert patched_write.called_once_with(SbuCommands.send_readable_timestamp_of_next_bu, timestamp)


@pytest.mark.parametrize(
    "measure_function, measure_command",
    [
        (SBU.measure_base_input_current, SbuCommands.measure_current),
        (SBU.measure_vcc3v_voltage, SbuCommands.measure_vcc3v),
        (SBU.measure_sbu_temperature, SbuCommands.measure_temperature),
    ],
)
def test_measure_quantities(
    sbu: SBU, mocker: MockerFixture, measure_function: Callable, measure_command: SbuCommand
) -> None:
    patched_measure = mocker.patch("base.hardware.sbu.sbu.SBU._measure", return_value=10)
    assert measure_function(sbu) == 10
    assert patched_measure.called_once_with(measure_command)


@pytest.mark.parametrize(
    "cmd", [SbuCommands.measure_current, SbuCommands.measure_temperature, SbuCommands.measure_vcc3v]
)
def test_measure(sbu: SBU, cmd: SbuCommand, mocker: MockerFixture) -> None:
    response_val = "xx10xx"
    patched_query = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.query", return_value=response_val)
    patched_extract = mocker.patch("base.hardware.sbu.sbu.SBU._extract_digits", return_value=10)
    patched_convert = mocker.patch("base.hardware.sbu.sbu.SBU._convert_measurement_result", return_value=10)
    sbu._measure(cmd)
    assert patched_query.called_once_with(cmd)
    assert patched_extract.called_once_with(response_val)
    assert patched_convert.called_once_with(cmd, 10)


@pytest.mark.parametrize(
    "input_value, output_value",
    [
        ("Writing 1 to CMP Register", 1),
        ("Writing 10 to CMP Register", 10),
        ("Writing 100 to CMP Register", 100),
        ("Writing 1000 to CMP Register", 1000),
        ("Writing 10000 to CMP Register", 10000),
    ],
)
def test_extract_digits(input_value: str, output_value: float) -> None:
    assert SBU._extract_digits(input_value) == output_value


@pytest.mark.parametrize(
    "cmd, raw_value, log_msg",
    [
        (SbuCommands.measure_current, 10, ""),
        (SbuCommands.measure_temperature, 10, ""),
        (SbuCommands.measure_vcc3v, 10, ""),
        (SbuCommands.abort_shutdown, None, "cannot convert"),
    ],
)
def test_convert_measurement_result(cmd: SbuCommand, raw_value: int, log_msg: str, caplog: LogCaptureFixture) -> None:
    if log_msg:
        with caplog.at_level(logging.WARNING):
            assert SBU._convert_measurement_result(cmd, raw_value) is None
        assert log_msg in caplog.text
    else:
        assert isinstance(SBU._convert_measurement_result(cmd, raw_value), float)


def test_request_shutdown(sbu: SBU, mocker: MockerFixture) -> None:
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    sbu.request_shutdown()
    assert patched_write.called_once_with(SbuCommands.request_shutdown)


def test_abort_shutdown(sbu: SBU, mocker: MockerFixture) -> None:
    patched_write = mocker.patch("base.hardware.sbu.communicator.SbuCommunicator.write")
    sbu.abort_shutdown()
    assert patched_write.called_once_with(SbuCommands.abort_shutdown)
