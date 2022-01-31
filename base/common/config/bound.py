from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Set
from weakref import WeakValueDictionary

from base.common.config.config_validator import ConfigValidator
from base.common.config.unbound import Config
from base.common.exceptions import ConfigSaveError, ConfigValidationError
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


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
        self._template_path: Path = self.base_path / "templates" / config_file_name
        self._initialized: bool = True
        self.reload()

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def template_path(self) -> Path:
        return self._template_path

    @classmethod
    def set_config_base_path(cls, base_dir: Path) -> None:
        cls.base_path = base_dir

    @classmethod
    def reload_all(cls) -> None:
        with ConfigValidator() as validator:
            for config in cls.__instances.values():
                config.reload()
                validator.validate(config)

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


def get_config(config_name: str) -> Config:
    return BoundConfig(config_name)
