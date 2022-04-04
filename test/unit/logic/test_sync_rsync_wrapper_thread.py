import logging
from pathlib import Path
from test.utils.patch_config import patch_config, patch_multiple_configs
from time import sleep
from types import TracebackType
from typing import Generator, Optional, Type

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture
from signalslot import Signal

from base.common.config import BoundConfig
from base.logic.backup.backup import Backup
from base.logic.backup.synchronisation.sync import Sync


class SyncMock(Sync):
    def __init__(self) -> None:
        self._pid: int = 1234

    @property
    def pid(self) -> int:
        return self._pid

    def __enter__(self) -> Generator[str, None, None]:  # type: ignore  # TODO: fix SyncMock
        generator = (i for i in ["first", "second"])
        yield from generator

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        pass


class SyncMockLoooongLoop(Sync):
    def __init__(self) -> None:
        self._pid = 1234
        self._exit_flag = False

    @property
    def pid(self) -> int:
        return self._pid

    def __enter__(self) -> Generator[int, None, None]:  # type: ignore  # TODO: fix SyncMock
        generator = (i for i in range(100000))  # long enough so the terminate can be called while busy
        while not self._exit_flag:
            yield next(generator)
            sleep(0.1)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        pass

    def terminate(self) -> None:
        self._exit_flag = True


def on_backup_finished(*args, **kwargs):  # type: ignore
    ...


@pytest.fixture
def rsync_wrapper_thread(mocker: MockFixture) -> Generator[Backup, None, None]:
    BoundConfig.set_config_base_path(Path().cwd() / "base/config")
    mocker.patch("signalslot.Signal.emit")
    rswt = Backup(on_backup_finished)
    # monkeypatch.setattr(sync.RsyncWrapperThread, '_ssh_rsync', SshRsyncMock(["first", "second"]))
    rswt._sync = SyncMock()
    yield rswt


@pytest.fixture
def rsync_wrapper_thread_loooong_loop(mocker: MockFixture) -> Generator[Backup, None, None]:
    BoundConfig.set_config_base_path(Path().cwd() / "base/config")
    mocker.patch("signalslot.Signal.emit")
    rswt = Backup(on_backup_finished)
    rswt._sync = SyncMockLoooongLoop()
    yield rswt


class TestRsyncWrapperThread:
    @pytest.mark.skip
    def test_run_rsync_wrapper_thread(self, rsync_wrapper_thread: Backup, caplog: LogCaptureFixture) -> None:
        with caplog.at_level(logging.DEBUG):
            rsync_wrapper_thread.start()
            rsync_wrapper_thread.join()
        assert "first" in caplog.text
        assert "second" in caplog.text
        assert "Backup finished!" in caplog.text
        assert Signal.emit.called_once_with()

    @pytest.mark.skip
    def test_terminate_rsync_wrapper_thread(self, rsync_wrapper_thread_loooong_loop: Backup) -> None:
        rsync_wrapper_thread_loooong_loop.start()
        assert rsync_wrapper_thread_loooong_loop.running
        rsync_wrapper_thread_loooong_loop.terminate()
        rsync_wrapper_thread_loooong_loop.join()
        assert not rsync_wrapper_thread_loooong_loop.running

    def test_get_pid(self) -> None:
        ...  # pid cannot be read, since "isinstance(self._ssh_rsync, SshRsync)" will fail
