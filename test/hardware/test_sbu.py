from pathlib import Path
import json
from random import random
from datetime import datetime

import pytest

from base.hardware.sbu import SBU, SbuUartFinder
from base.common.config import Config


@pytest.fixture(scope="session")
def sbu(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("sbu_test_config_dir")
    config_path = Path("/home/base/python.base/base/config/")
    config_test_path = Path(tmpdir.mkdir("config"))
    with open(config_path/"sbu.json", "r") as src, open(config_test_path/"sbu.json", "w") as dst:
        drive_config_data = json.load(src)
        json.dump(drive_config_data, dst)
    Config.set_config_base_path(config_test_path)
    yield SBU()


@pytest.mark.slow
def test_sbu_uart_finder():
    assert SbuUartFinder().get_sbu_uart_interface().startswith('/dev/ttyS')


def test_write_to_display(sbu):
    sbu.write_to_display("Write to Display", f"Random: {random():07f}")


@pytest.mark.slow
def test_set_display_brightness(sbu):
    for brightness in range(0, 101, 10):
        sbu.set_display_brightness_percent(brightness)


@pytest.mark.slow
def test_set_led_brightness(sbu):
    for brightness in range(0, 101, 10):
        sbu.set_led_brightness_percent(brightness)


def test_send_seconds_to_next_bu(sbu):
    seconds = 128
    sbu.send_seconds_to_next_bu(seconds)

def test_send_readable_timestamp(sbu):
    timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')
    sbu.send_readable_timestamp(timestamp)
