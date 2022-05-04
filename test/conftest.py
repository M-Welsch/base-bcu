import sys
from pathlib import Path
from platform import machine
from typing import Generator

import pytest
from py import path


def pytest_configure() -> None:
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """

    if machine() not in ["armv6l", "armv7l"]:
        from importlib import import_module

        sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")
        print("Not on SBC")


@pytest.fixture(autouse=True)
def init_logger_factory(tmpdir: path.local) -> Generator[None, None, None]:
    from base.common.logger import LoggerFactory

    LoggerFactory(log_path=Path(tmpdir), parent_logger_name="BaSe_test", development_mode=True)
    yield
    LoggerFactory._LoggerFactory__instance = None  # type: ignore
