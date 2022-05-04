import logging
from datetime import datetime
from os.path import getctime
from pathlib import Path
from typing import Any, Optional, Tuple, Type


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


class CachingFileHandler(logging.FileHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._message_cache: LineBuffer = LineBuffer(5)

    def emit(self, record: logging.LogRecord) -> None:
        self._message_cache.push(record.msg)
        super().emit(record)

    @property
    def message_cache(self) -> Tuple[str, ...]:
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
    __logs_directory = Path.cwd() / "base/log"

    def __init__(self, log_path: Path, parent_logger_name: str, development_mode: bool = False) -> None:
        """Virtually private constructor."""
        if LoggerFactory.__instance is None:
            self._logs_directory = log_path
            self.__class__.__parent_logger_name = parent_logger_name
            self._development_mode: bool = development_mode
            self._parent_logger: logging.Logger
            self._setup_project_logger()
            LoggerFactory.__instance = self
        else:
            raise RuntimeError(f"{self.__class__.__name__} is a singleton and was already instantiated!")

    @classmethod
    def logs_directory(cls) -> Path:
        return cls.__logs_directory

    @classmethod
    def get_last_lines(cls) -> Tuple[str, ...]:
        assert isinstance(cls.__file_handler, CachingFileHandler)
        return cls.__file_handler.message_cache

    @classmethod
    def get_warning_count(cls) -> int:
        assert isinstance(cls.__warning_file_handler, WarningFileHandler)
        return cls.__warning_file_handler.warning_count

    def _setup_project_logger(self) -> None:
        self._parent_logger = logging.getLogger(self.__class__.__parent_logger_name)
        self._parent_logger.setLevel(logging.DEBUG if self._development_mode else logging.INFO)
        self._setup_file_handler(
            handler_class=CachingFileHandler,
            log_file_name=datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"),
            log_level=logging.DEBUG
        )
        self._setup_file_handler(
            handler_class=WarningFileHandler,
            log_file_name="warnings.log",
            log_level=logging.WARNING
        )
        self._setup_console_handler()

    def _setup_file_handler(self, handler_class: Type[logging.Handler], log_file_name: str, log_level: int) -> None:
        self._logs_directory.mkdir(exist_ok=True, parents=True)
        current_log_name = self._logs_directory / log_file_name
        self.__class__.__file_handler = handler_class(current_log_name.as_posix())
        self.__class__.__file_handler.setLevel(log_level)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(name)s: %(message)s")
        formatter.datefmt = "%m.%d.%Y %H:%M:%S"
        self.__class__.__file_handler.setFormatter(formatter)
        self._parent_logger.addHandler(self.__class__.__file_handler)

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
            cls(log_path=Path("/tmp/logs"), parent_logger_name="BaSe", development_mode=True)
            print("WARNING: Logger has been initialized with default values. Not for production.")
        return logging.getLogger(f"{cls.__parent_logger_name}.{module_name}")


def most_recent_logfile() -> Optional[Path]:
    return max(LoggerFactory.logs_directory().iterdir(), key=getctime, default=None)  # type: ignore
