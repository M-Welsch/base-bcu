import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Type

from base.common.config import Config


def patch_config(class_: Type, config_content: Dict[str, Any], read_only: bool = True) -> None:
    sys.modules[class_.__module__].get_config = lambda _: Config(config_content, read_only=read_only)  # type: ignore


def patch_multiple_configs(class_: Type, config_content: Dict[str, Dict[str, Any]]) -> None:
    def make_substitute_config(file_name: str) -> Config:
        config = Config(config_content[file_name])
        config["reload"] = lambda: None
        return config

    sys.modules[class_.__module__].get_config = lambda file_name: make_substitute_config(file_name)  # type: ignore


def derive_mock_string(func: Callable) -> str:
    return f"{func.__module__}.{func.__qualname__}"


def create_file_with_random_data(path: Path, size_bytes: int) -> None:
    with open(path, "wb") as fout:
        fout.write(os.urandom(size_bytes))
