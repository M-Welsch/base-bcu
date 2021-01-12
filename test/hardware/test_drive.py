from pathlib import Path

import pytest

from base.hardware.drive import Drive
from base.common.config import Config


@pytest.fixture
def drive():
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield Drive()


def test_mount(drive):
    drive.mount()
    assert Path(drive._device_info.path).is_mount()


def test_unmount(drive):
    if drive._device_info is not None:
        drive.unmount()
        assert not Path(drive._device_info.path).is_mount()
