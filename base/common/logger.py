from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, List, Optional, Tuple


class LineBuffer(list):
    def __init__(self, maximum_size: int) -> None:
        super().__init__()
        self._maximum_size: int = maximum_size

    def push(self, item: str) -> None:
        if not isinstance(item, str):
            raise ValueError(f"Item has to be of type str, but is of type {type(item)}")
        if len(self) >= self._maximum_size:
            del self[0]
        self.append(str(item))

    @property
    def content(self) -> Tuple[str, ...]:
        return tuple(self)


class BaseConsoleHandler(logging.StreamHandler):
    def __init__(self, parent: logging.Logger, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s: %(name)s: %(message)s")
        formatter.datefmt = "%m.%d.%Y %H:%M:%S"
        self.setFormatter(formatter)
        parent.addHandler(self)


class BaseFileHandler(logging.FileHandler):
    def __init__(self, log_file_path: Path, parent: logging.Logger, log_level: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(log_file_path.as_posix(), *args, **kwargs)
        self._log_file_path = log_file_path
        self.setLevel(log_level)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(name)s: %(message)s")
        formatter.datefmt = "%m.%d.%Y %H:%M:%S"
        self.setFormatter(formatter)
        parent.addHandler(self)

    @property
    def log_file_path(self) -> Path:
        return self._log_file_path


class CachingFileHandler(BaseFileHandler):
    def __init__(self, log_level: int = logging.DEBUG, *args: Any, **kwargs: Any) -> None:
        super().__init__(log_level=log_level, *args, **kwargs)  # type: ignore
        self._message_cache: LineBuffer = LineBuffer(5)

    def emit(self, record: logging.LogRecord) -> None:
        self._message_cache.push(record.msg)
        super().emit(record)

    @property
    def message_cache(self) -> Tuple[str, ...]:
        return self._message_cache.content


class WarningFileHandler(BaseFileHandler):
    def __init__(self, log_file_path: Path, *args: Any, **kwargs: Any) -> None:
        super().__init__(log_file_path=log_file_path, log_level=logging.WARNING, *args, **kwargs)  # type: ignore
        self._warning_counter: int = self._count_lines(log_file_path)

    def emit(self, record: logging.LogRecord) -> None:
        self._warning_counter += 1
        super().emit(record)

    @property
    def warning_count(self) -> int:
        return self._warning_counter

    @staticmethod
    def _count_lines(log_path: Path) -> int:
        if not log_path.is_file():
            return 0
        with open(log_path, "r") as f:
            return sum([1 for _ in f])


class CriticalHandler(logging.StreamHandler):
    def __init__(self, parent: logging.Logger):
        super().__init__()
        self.setLevel(logging.CRITICAL)
        self._formatter = logging.Formatter("%(asctime)s %(levelname)s: %(name)s: %(message)s")
        self._formatter.datefmt = "%m.%d.%Y %H:%M:%S"
        self.setFormatter(self._formatter)
        parent.addHandler(self)
        self._critical_records: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self._critical_records.append(record)

    @property
    def critical_messages(self) -> Generator[str, None, None]:
        return (self._formatter.formatMessage(record) for record in self._critical_records)


class LoggerFactory:
    __instance: Optional[LoggerFactory] = None
    __logs_directory = Path.cwd() / "base/log"
    __project_logger: Optional[logging.Logger] = None
    __console_handler: Optional[BaseConsoleHandler] = None
    __file_handler: Optional[CachingFileHandler] = None
    __warning_file_handler: Optional[WarningFileHandler] = None
    __critical_handler: Optional[CriticalHandler] = None

    def __init__(self, log_path: Path, parent_logger_name: str, development_mode: bool = False) -> None:
        """Virtually private constructor."""
        if LoggerFactory.__instance is None:
            self.__class__.__logs_directory = log_path
            self._setup(parent_logger_name, development_mode)
            LoggerFactory.__instance = self
        else:
            raise RuntimeError(f"{self.__class__.__name__} is a singleton and was already instantiated!")

    @classmethod
    def logs_directory(cls) -> Path:
        return cls.__logs_directory

    @classmethod
    def current_log_file(cls) -> Path:
        assert isinstance(cls.__file_handler, CachingFileHandler)
        return cls.__file_handler.log_file_path

    @classmethod
    def current_warning_log_file(cls) -> Path:
        assert isinstance(cls.__warning_file_handler, WarningFileHandler)
        return cls.__warning_file_handler.log_file_path

    @classmethod
    def get_last_lines(cls) -> Tuple[str, ...]:
        assert isinstance(cls.__file_handler, CachingFileHandler)
        return cls.__file_handler.message_cache

    @classmethod
    def get_warning_count(cls) -> int:
        assert isinstance(cls.__warning_file_handler, WarningFileHandler)
        return cls.__warning_file_handler.warning_count

    @classmethod
    def get_critical_messages(cls) -> Generator[str, None, None]:
        assert isinstance(cls.__critical_handler, CriticalHandler)
        return cls.__critical_handler.critical_messages

    @classmethod
    def _setup(cls, parent_logger_name: str, development_mode: bool) -> None:
        cls.__project_logger = logging.getLogger(parent_logger_name)
        cls.__project_logger.setLevel(logging.DEBUG if development_mode else logging.INFO)
        cls.__console_handler = BaseConsoleHandler(parent=cls.__project_logger)
        cls.__file_handler = CachingFileHandler(
            log_file_path=cls.__logs_directory / datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"),
            parent=cls.__project_logger,
        )
        cls.__warning_file_handler = WarningFileHandler(
            log_file_path=cls.__logs_directory / "warnings.log", parent=cls.__project_logger
        )
        cls.__critical_handler = CriticalHandler(parent=cls.__project_logger)

    @classmethod
    def get_logger(cls, module_name: str) -> logging.Logger:
        if cls.__instance is None:
            cls(log_path=Path("/tmp/logs"), parent_logger_name="BaSe", development_mode=True)
            print("WARNING: Logger has been initialized with default values. Not for production.")
        assert isinstance(cls.__project_logger, logging.Logger)
        return logging.getLogger(f"{cls.__project_logger.name}.{module_name}")
