import json
from datetime import datetime
from pathlib import Path
from random import random

import pytest

from base.common.config import Config
from base.hardware.sbu.sbu import SBU, WakeupReason
from base.hardware.sbu.sbu_uart_finder import SbuUartFinder


@pytest.fixture(scope="session")
def sbu(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("sbu_test_config_dir")
    config_path = Path("/home/base/python.base/base/config/")
    config_test_path = Path(tmpdir.mkdir("config"))
    with open(config_path / "sbu.json", "r") as src, open(config_test_path / "sbu.json", "w") as dst:
        drive_config_data = json.load(src)
        json.dump(drive_config_data, dst)
    Config.set_config_base_path(config_test_path)
    yield SBU()


@pytest.mark.slow
def test_sbu_uart_finder(sbu):
    assert str(SbuUartFinder().get_sbu_uart_interface()).startswith("/dev/ttyS")


def test_write_to_display(sbu: SBU):
    sbu.write_to_display("Write to Display", f"Random: {random():07f}")


def test_set_display_brightness(sbu):
    for brightness in range(0, 101, 10):
        sbu.set_display_brightness_percent(brightness)


def test_set_led_brightness(sbu):
    for brightness in range(0, 101, 10):
        sbu.set_led_brightness_percent(brightness)


def test_send_seconds_to_next_bu(sbu):
    seconds = 128
    sbu.send_seconds_to_next_bu(seconds)


def test_send_readable_timestamp(sbu):
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    sbu.send_readable_timestamp(timestamp)


def test_current_measurement(sbu):
    print(sbu.measure_base_input_current())


def test_vcc3v_voltage_measurement(sbu):
    print(sbu.measure_vcc3v_voltage())


def test_sbu_temperature_measurement(sbu):
    print(sbu.measure_sbu_temperature())


@pytest.mark.parametrize(
    "code, reason", [("WR_BACKUP", WakeupReason.BACKUP_NOW), ("WR_CONFIG", WakeupReason.CONFIGURATION)]
)
def test_wakeup_reason_backup_now(sbu, code, reason):
    sbu.set_wakeup_reason(code)
    received_reason: WakeupReason = sbu.request_wakeup_reason()
    assert received_reason == reason
    received_reason: WakeupReason = sbu.request_wakeup_reason()
    assert received_reason == WakeupReason.NO_REASON