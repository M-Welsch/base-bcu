import logging
from typing import Generator

import pytest
from _pytest.logging import LogCaptureFixture

from base.common.logger import (
    BaseConsoleHandler,
    CachingFileHandler,
    CriticalHandler,
    LoggerFactory,
    WarningFileHandler,
)


@pytest.fixture()
def log() -> Generator[logging.Logger, None, None]:
    yield LoggerFactory.get_logger(__name__)


def test_initialization(log: logging.Logger) -> None:
    assert isinstance(LoggerFactory._LoggerFactory__instance, LoggerFactory)  # type: ignore
    assert isinstance(LoggerFactory._LoggerFactory__project_logger, logging.Logger)  # type: ignore
    assert isinstance(LoggerFactory._LoggerFactory__console_handler, BaseConsoleHandler)  # type: ignore
    assert isinstance(LoggerFactory._LoggerFactory__file_handler, CachingFileHandler)  # type: ignore
    assert isinstance(LoggerFactory._LoggerFactory__warning_file_handler, WarningFileHandler)  # type: ignore
    assert isinstance(LoggerFactory._LoggerFactory__critical_handler, CriticalHandler)  # type: ignore


def test_console_handler(log: logging.Logger, caplog: LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        log.debug("Debug")
        log.info("Info")
        log.warning("Warning")
        log.error("Error")
        log.critical("Critical")
    messages = caplog.text.strip().split("\n")
    assert len(messages) == 5
    assert "Debug" in messages[0]
    assert "Info" in messages[1]
    assert "Warning" in messages[2]
    assert "Error" in messages[3]
    assert "Critical" in messages[4]


def test_file_handler(log: logging.Logger) -> None:
    log.debug("Debug")
    log.info("Info")
    log.warning("Warning")
    log.error("Error")
    log.critical("Critical")
    with open(LoggerFactory.current_log_file(), "r") as f:
        lines = f.readlines()
        assert len(lines) == 5
        assert f"DEBUG: BaSe_test.{__name__}: Debug" in lines[0]
        assert f"INFO: BaSe_test.{__name__}: Info" in lines[1]
        assert f"WARNING: BaSe_test.{__name__}: Warning" in lines[2]
        assert f"ERROR: BaSe_test.{__name__}: Error" in lines[3]
        assert f"CRITICAL: BaSe_test.{__name__}: Critical" in lines[4]


def test_warning_file_handler(log: logging.Logger) -> None:
    log.debug("Debug")
    log.info("Info")
    log.warning("Warning")
    log.error("Error")
    log.critical("Critical")
    with open(LoggerFactory.current_warning_log_file(), "r") as f:
        lines = f.readlines()
        assert len(lines) == 3
        assert f"WARNING: BaSe_test.{__name__}: Warning" in lines[0]
        assert f"ERROR: BaSe_test.{__name__}: Error" in lines[1]
        assert f"CRITICAL: BaSe_test.{__name__}: Critical" in lines[2]


def test_critical_messages(log: logging.Logger) -> None:
    log.debug("Debug")
    log.info("Info")
    log.warning("Warning")
    log.error("Error")
    log.critical("Critical")
    critical_messages = list(LoggerFactory.get_critical_messages())
    assert len(critical_messages) == 1
    assert f"CRITICAL: BaSe_test.{__name__}: Critical" in critical_messages[0]
