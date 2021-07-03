import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple


class LineBuffer(list):
    def __init__(self, size: int) -> None:
        super().__init__()
        self._size: int = size

    def push(self, item: str) -> None:
        if len(self) >= self._size:
            del self[0]
        self.append(str(item))

    @property
    def content(self) -> Tuple[str]:
        return tuple(self)


class CachingFileHandler(logging.FileHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._message_cache: LineBuffer = LineBuffer(5)

    def emit(self, record: logging.LogRecord) -> None:
        self._message_cache.push(record.msg)
        super().emit(record)

    @property
    def message_cache(self) -> Tuple[str]:
        return self._message_cache.content


class WarningFileHandler(logging.FileHandler):
    def __init__(self, log_path: Path, *args: Any, **kwargs: Any) -> None:
        super().__init__(log_path, *args, **kwargs)
        self._warning_counter: int = self._count_lines(log_path)

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


class LoggerFactory:
    __instance = None
    __parent_logger_name: Optional[str] = None
    __file_handler: Optional[CachingFileHandler] = None
    __warning_file_handler: Optional[WarningFileHandler] = None

    def __init__(self, config_path: Path, parent_logger_name: str, development_mode: bool = False) -> None:
        """Virtually private constructor."""
        if LoggerFactory.__instance is None:
            self._logs_directory = self.get_logs_directory(config_path)
            self.__class__.__parent_logger_name = parent_logger_name
            self._development_mode: bool = development_mode
            self._current_log_name: Path = Path()
            self._current_warning_log_name: Path = Path()
            self._parent_logger: logging.Logger
            self._file_handler: CachingFileHandler
            self._warning_file_handler: WarningFileHandler
            self._setup_project_logger()
            LoggerFactory.__instance = self
        else:
            raise RuntimeError(f"{self.__class__.__name__} is a singleton and was already instantiated!")

    @staticmethod
    def get_logs_directory(config_path: Path) -> Path:
        with open(config_path / "base.json", "r") as cfg_file:
            logs_directory = json.load(cfg_file)["logs_directory"]
        return Path.cwd() / Path(logs_directory)

    @classmethod
    def get_last_lines(cls) -> Tuple[str]:
        return cls.__file_handler.message_cache

    @classmethod
    def get_warning_count(cls) -> int:
        return cls.__warning_file_handler.warning_count

    def _setup_project_logger(self) -> None:
        self._parent_logger = logging.getLogger(self.__class__.__parent_logger_name)
        self._parent_logger.setLevel(logging.DEBUG if self._development_mode else logging.INFO)
        self._setup_file_handler()
        self._setup_warning_file_handler()
        self._setup_console_handler()

    def _setup_file_handler(self) -> None:
        self._logs_directory.mkdir(exist_ok=True)
        self._current_log_name = self._logs_directory / datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
        self.__class__.__file_handler = CachingFileHandler(self._current_log_name)
        self.__class__.__file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(name)s: %(message)s")
        formatter.datefmt = "%m.%d.%Y %H:%M:%S"
        self.__class__.__file_handler.setFormatter(formatter)
        self._parent_logger.addHandler(self.__class__.__file_handler)

    def _setup_warning_file_handler(self) -> None:
        self._logs_directory.mkdir(exist_ok=True)
        self._current_warning_log_name = self._logs_directory / Path("warnings.log")
        self.__class__.__warning_file_handler = WarningFileHandler(self._current_log_name)
        self.__class__.__warning_file_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(name)s: %(message)s")
        formatter.datefmt = "%m.%d.%Y %H:%M:%S"
        self.__class__.__warning_file_handler.setFormatter(formatter)
        self._parent_logger.addHandler(self.__class__.__warning_file_handler)

    def _setup_console_handler(self) -> None:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s: %(name)s: %(message)s")
        formatter.datefmt = "%m.%d.%Y %H:%M:%S"
        handler.setFormatter(formatter)
        self._parent_logger.addHandler(handler)

    @classmethod
    def get_logger(cls, module_name: str) -> logging.Logger:
        if cls.__instance is None:
            raise RuntimeError(f"Instantiate {cls.__name__} first.")
        return logging.getLogger(f"{cls.__parent_logger_name}.{module_name}")
