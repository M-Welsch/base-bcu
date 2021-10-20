from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set
from weakref import WeakValueDictionary

from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class ConfigValidationError(Exception):
    pass


class ConfigSaveError(Exception):
    pass


class Config(dict):
    def __init__(self, data: Dict[str, Any], read_only: bool = True, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._read_only: bool = read_only
        self._initialized: bool = True
        self.update(data)

    def assert_keys(self, keys: Set[str]) -> None:
        missing_keys = keys - set(self.keys())
        if missing_keys:
            raise ConfigValidationError(f"Keys {missing_keys} are missing.")

    @property
    def is_read_only(self) -> bool:
        return self._read_only

    def __getattr__(self, name: str) -> Any:
        if name in self.keys():
            return self[name]
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.keys() and self._read_only:
            raise RuntimeError(f"'{type(self).__name__}' object is read-only")
        elif name in self.keys() and not self._read_only:
            self[name] = value
        elif name not in self.keys() and "_initialized" not in self.__dict__:
            self.__dict__[name] = value
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class BoundConfig(Config):
    base_path = Path("base/config/")
    __instances: WeakValueDictionary[str, BoundConfig] = WeakValueDictionary()

    def __new__(cls, config_file_name: str, *args: Any, **kwargs: Any) -> BoundConfig:
        if config_file_name in cls.__instances:
            return cls.__instances[config_file_name]
        self: BoundConfig = super().__new__(cls)
        cls.__instances[config_file_name] = self
        return self

    def __init__(self, config_file_name: str, read_only: bool = True, *args: Any, **kwargs: Any) -> None:
        super(Config, self).__init__(*args, **kwargs)
        self._read_only: bool = read_only
        self._config_path: Path = self.base_path / config_file_name
        self._initialized: bool = True
        self.reload()

    @classmethod
    def set_config_base_path(cls, base_dir: Path) -> None:
        cls.base_path = base_dir

    @classmethod
    def reload_all(cls) -> None:
        for config in cls.__instances.values():
            config.reload()

    def reload(self, **kwargs):  # type: ignore
        LOG.info(f"reloading config: {self._config_path}")
        with open(self._config_path, "r") as jf:
            self.update(json.load(jf))

    def save(self) -> None:
        LOG.info(f"saving config: {self._config_path}")
        if self._read_only:
            raise ConfigSaveError("This config is read-only and is therefore not savable")
        with open(self._config_path, "w") as jf:
            json.dump(self, jf)

    def assert_keys(self, keys: Set[str]) -> None:
        missing_keys = keys - set(self.keys())
        if missing_keys:
            raise ConfigValidationError(f"Keys {missing_keys} are missing in {self._config_path}.")
