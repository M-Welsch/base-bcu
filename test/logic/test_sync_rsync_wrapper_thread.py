import logging
from time import sleep

import pytest
from _pytest.logging import LogCaptureFixture
from pathlib import Path
from signalslot import Signal

from base.logic.backup.synchronisation.sync_thread import SyncThread
from base.common.config import Config


class SshRsyncMock:
    def __init__(self):
        self.pid = 1234

    def __enter__(self):
        generator = (i for i in ["first", "second"])
        yield from generator

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class SshRsyncMockLoooongLoop:
    def __init__(self):
        self.pid = 1234
        self._exit_flag = False

    def __enter__(self):
        generator = (i for i in range(100000))  # long enough so the terminate can be called while busy
        while not self._exit_flag:
            yield next(generator)
            sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def terminate(self) -> None:
        self._exit_flag = True


@pytest.fixture
def rsync_wrapper_thread(mocker):
    Config.set_config_base_path(Path('python.base/base/config'))
    mocker.patch('signalslot.Signal.emit')
    rswt = SyncThread(local_target_location=Path(), source_location=Path())
    # monkeypatch.setattr(sync.RsyncWrapperThread, '_ssh_rsync', SshRsyncMock(["first", "second"]))
    rswt._ssh_rsync = SshRsyncMock()
    yield rswt


@pytest.fixture
def rsync_wrapper_thread_loooong_loop(mocker):
    Config.set_config_base_path(Path('python.base/base/config'))
    mocker.patch('signalslot.Signal.emit')
    rswt = SyncThread(local_target_location=Path(), source_location=Path())
    rswt._ssh_rsync = SshRsyncMockLoooongLoop()
    yield rswt


class TestRsyncWrapperThread:
    def test_run_rsync_wrapper_thread(self, rsync_wrapper_thread: SyncThread, caplog: LogCaptureFixture):
        with caplog.at_level(logging.DEBUG):
            rsync_wrapper_thread.start()
            rsync_wrapper_thread.join()
        assert "first" in caplog.text
        assert "second" in caplog.text
        assert "Backup finished!" in caplog.text
        Signal.emit.assert_called_once_with()

    def test_terminate_rsync_wrapper_thread(self, rsync_wrapper_thread_loooong_loop: SyncThread):
        rsync_wrapper_thread_loooong_loop.start()
        assert rsync_wrapper_thread_loooong_loop.running
        rsync_wrapper_thread_loooong_loop.terminate()
        rsync_wrapper_thread_loooong_loop.join()
        assert not rsync_wrapper_thread_loooong_loop.running

    def test_get_pid(self):
        ...  # pid cannot be read, since "isinstance(self._ssh_rsync, SshRsync)" will fail
