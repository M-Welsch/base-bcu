from pathlib import Path
from threading import Timer
from time import time
from typing import Generator

import pytest
from pytest_mock import MockFixture

import base.logic.backup.synchronisation.sync
from base.logic.backup.synchronisation.sync import Sync


@pytest.fixture
def sync() -> Generator[Sync, None, None]:
    yield Sync(Path(), Path())


@pytest.mark.parametrize("sleep_time", [0.1, 0.3])
def test_start_process(sync: Sync, mocker: MockFixture, sleep_time: float) -> None:
    mocker.patch("base.logic.backup.synchronisation.sync.Sync._get_command", return_value=f"sleep {sleep_time}")
    time_start = time()
    with sync as _sync:
        pass
    assert time() - time_start > sleep_time


@pytest.mark.parametrize("sleep_time", [0.5])
def test_terminate_process(sync: Sync, mocker: MockFixture, sleep_time: float) -> None:
    mocker.patch("base.logic.backup.synchronisation.sync.Sync._get_command", return_value=f"sleep {sleep_time}")
    time_start = time()
    with sync as _sync:
        t = Timer(0.1, lambda: sync.terminate())
        t.start()
    assert time() - time_start < sleep_time
