from datetime import datetime
import logging
from pathlib import Path

from base.common.config import Config


class LoggerFactory:
    _parent_logger_name = None

    @classmethod
    def setup(cls, parent_logger_name, development_mode=False):
        if cls._parent_logger_name is not None:
            raise RuntimeError(f"{cls.__name__}.setup() can only be called once.")
        cls._parent_logger_name = parent_logger_name
        cls._setup_project_logger(development_mode)

    @classmethod
    def _setup_project_logger(cls, development_mode):
        logger = logging.getLogger(cls._parent_logger_name)
        logger.setLevel(logging.DEBUG if development_mode else logging.INFO)
        cls._setup_file_handler(logger, development_mode)
        cls._setup_console_handler(logger, development_mode)

    @staticmethod
    def _setup_file_handler(logger, development_mode):
        config: Config = Config("base.json")
        logs_dir = Path.cwd()/Path(config.logs_directory)
        logs_dir.mkdir(exist_ok=True)
        logfile = logs_dir / datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log')
        handler = logging.FileHandler(logfile)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(name)s: %(message)s')
        formatter.datefmt = '%m.%d.%Y %H:%M:%S'
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    @staticmethod
    def _setup_console_handler(logger, development_mode):
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s: %(name)s: %(message)s')
        formatter.datefmt = '%m.%d.%Y %H:%M:%S'
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    @classmethod
    def get_logger(cls, module_name):
        if cls._parent_logger_name is None:
            raise RuntimeError(f"Call {cls.__name__}.setup() first.")
        return logging.getLogger(f"{cls._parent_logger_name}.{module_name}")
