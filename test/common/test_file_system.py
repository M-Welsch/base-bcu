from subprocess import Popen, PIPE
from threading import Thread
from time import sleep
from pathlib import Path
import pytest

from base.common.config import Config
from base.common.file_system import FileSystemWatcher
from base.hardware.drive import Drive


class MountMockup(Thread):
    def __init__(self, device):
        super().__init__()
        self._device = device

    def run(self):
        sleep(0.5)
        command = f"mount -t vfat {self._device} /media/BackupHDD".split() # use usb-Stick
        Popen(command, stdout=PIPE, stderr=PIPE)


@pytest.fixture()
def file_system_watcher():
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield FileSystemWatcher(5)


def test_file_system_watcher(file_system_watcher):
    file_system_watcher.add_watches(["/dev"])
    mount_mockup = MountMockup("/dev/sda1")
    mount_mockup.start()
    file_system_watcher._watch_until_timeout()