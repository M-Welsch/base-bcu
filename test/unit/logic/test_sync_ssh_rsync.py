from pathlib import Path
from subprocess import PIPE, Popen
from test.utils.patch_config import patch_multiple_configs
from time import sleep
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pytest_mock import MockFixture

from base.common.config import BoundConfig
from base.logic.backup.synchronisation.rsync_command import RsyncCommand
from base.logic.backup.synchronisation.sync import Sync


def patch_rsync_command_configs() -> None:
    patch_multiple_configs(
        RsyncCommand,
        {
            "nas.json": {"ssh_host": "192.168.178.64", "ssh_port": 22, "ssh_user": "root"},
            "sync.json": {"protocol": "ssh", "ssh_keyfile_path": "/home/base/.ssh/id_rsa"},
        },
    )


@pytest.fixture
def sync() -> Generator[Sync, None, None]:
    BoundConfig.set_config_base_path(Path() / "base/config")
    sync = Sync(local_target_location=Path(), source_location=Path())
    stimulus = ["echo", "-e", "Status Line 1\n\nExit"]
    sync._process = Popen(stimulus, stdout=PIPE, stderr=PIPE, bufsize=0, universal_newlines=True)
    yield sync


@pytest.fixture
def sync_process_terminate_mocked(mocker: MockFixture) -> Generator[Sync, None, None]:
    BoundConfig.set_config_base_path(Path() / "base/config")
    patch_rsync_command_configs()
    sync = Sync(local_target_location=Path(), source_location=Path())
    mocker.patch("base.logic.backup.synchronisation.sync.Sync.terminate")
    yield sync


@pytest.fixture
def sync_process(mocker: MockFixture) -> Generator[Sync, None, None]:
    mocker.patch("base.logic.backup.synchronisation.sync.Sync._get_command", return_value="/bin/sleep 0.3")
    BoundConfig.set_config_base_path(Path() / "base/config")
    sync = Sync(local_target_location=Path(), source_location=Path())
    yield sync


class TestSshRsync:
    def test_output_generator(self, sync: Sync, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("base.logic.backup.synchronisation.sync.parse_line_to_status", lambda line, status: line)
        output_generator = sync._output_generator()
        assert next(output_generator) == "Status Line 1"
        assert next(output_generator) == ""
        assert next(output_generator) == "Exit"
        with pytest.raises(StopIteration):
            next(output_generator)

    def test_start_stop_sync_process(self, sync_process_terminate_mocked: Sync) -> None:
        with sync_process_terminate_mocked:
            sleep(0.1)
        assert sync_process_terminate_mocked.terminate.called_once_with()  # type: ignore

    def test_process_termination_by_end_of_context_manager(self, sync_process: Sync) -> None:
        with sync_process:
            sleep(0.1)
        if isinstance(sync_process._process, Popen):
            sync_process._process.wait()
        with pytest.raises(ProcessLookupError):
            sync_process.terminate()

    def test_manual_process_termination(self, sync_process: Sync) -> None:
        with sync_process:
            sleep(0.01)
            assert isinstance(sync_process._process, Popen)
            assert sync_process._process.poll() is None
            sync_process.terminate()
            sync_process._process.wait(0.1)
            assert sync_process._process.poll() is not None

    def test_parse_line_to_status(self) -> None:
        ...
