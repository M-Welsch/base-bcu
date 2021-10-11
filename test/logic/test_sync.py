import pytest
import pytest_mock
from pathlib import Path
from signalslot import Signal

from base.logic.backup.sync import RsyncWrapperThread


class SshRsyncMock:
    def __init__(self):
        self.pid = 1234

    def __enter__(self):
        return (i for i in range(10))

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class SignalMock:
    def __init__(self):
        self.is_being_run = False

    def emit(self):
        self.is_being_run = True


@pytest.fixture
def rsync_wrapper_thread(mocker):
    mocker.patch('signalslot.Signal.emit')
    local_target_location_mock = Path()
    source_location_mock = Path()
    rswt = RsyncWrapperThread(local_target_location_mock, source_location_mock)
    # rswt.terminated = SignalMock()
    rswt._ssh_rsync = SshRsyncMock()
    yield rswt


class TestRsyncWrapperThread:
    def test_run_rsync_wrapper_thread(self, rsync_wrapper_thread: RsyncWrapperThread):
        rsync_wrapper_thread.run()
        rsync_wrapper_thread.join()
        Signal.emit.assert_called_once_with()
