from __future__ import annotations

import json
import re
from pathlib import Path
from pydoc import locate
from types import TracebackType
from typing import Dict, Optional, Type

from base.common.config import BoundConfig, Config, ConfigValidationError


class ConfigValidator:
    type_to_check = {"str": str, "pathlib.Path": str, "int": int, "float": float, "bool": bool}
    validation_pipeline_map = {
        "str": ["_check_type_validity", "_check_regex"],
        "pathlib.Path": ["_check_type_validity", "_check_path_resolve"],
        "int": ["_check_type_validity", "_check_range"],
        "float": ["_check_type_validity", "_check_range"],
        "bool": ["_check_type_validity"],
    }

    def __init__(self) -> None:
        self.invalid_keys: Dict[str, str] = {}

    def __enter__(self) -> ConfigValidator:
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        if self.invalid_keys:
            raise ConfigValidationError(self.invalid_keys)

    def _check_type_validity(self, key: str, template_data: dict, config: Config) -> None:
        valid_type = locate(template_data["type"])
        if type(config[key]) is not self.type_to_check[template_data["type"]]:
            self.invalid_keys[key] = (
                f"Value of key '{key}' has invalid type {type(config[key])} "
                f"in config file {config.config_path}. Should be: {valid_type}"
            )

    def _check_regex(self, key: str, template_data: dict, config: Config) -> None:
        if not re.fullmatch(pattern=template_data["valid"], string=config[key]):
            self.invalid_keys[key] = (
                f"Value {config[key]} of key {key} in config file {config.config_path} "
                f"does not match the regex {template_data['valid']}"
            )

    def _check_range(self, key: str, template_data: dict, config: Config) -> None:
        minimum = template_data["valid"]["min"]
        maximum = template_data["valid"]["max"]
        if minimum is not None and config[key] < minimum:
            self.invalid_keys[
                key
            ] = f"Value of key '{key}' in config file {config.config_path} must be greater than {minimum}"
        if maximum is not None and config[key] > maximum:
            self.invalid_keys[
                key
            ] = f"Value of key '{key}' in config file {config.config_path} must be less than {maximum}"

    def _check_path_resolve(self, key: str, template_data: dict, config: Config) -> None:
        try:
            Path(config[key]).resolve()
        except ValueError:
            self.invalid_keys[key] = (
                f"Value {config[key]} of key {key} in config file {config.config_path} " f"is not a valid path"
            )

    def validate(self, config: Config) -> None:
        template = self.get_template(config.template_path)
        self._validate_items(template, config)

    @staticmethod
    def get_template(template_path: Path) -> dict:
        with open(template_path, "r") as template_file:
            result: dict = json.load(template_file)
            return result

    def _validate_items(self, template: dict, config: Config) -> None:
        for template_key, template_data in template.items():
            self._validate_item(config, template_data, template_key)

    def _validate_item(self, config, template_key: str, template_data: dict) -> None:
        if self._check_validation_required(config, template_key, template_data):
            for step_name in self.validation_pipeline_map[template_data["type"]]:
                step_func = getattr(self, step_name)
                step_func(template_key, template_data, config)

    def _check_validation_required(self, config: Config, template_key: str, template_data: dict) -> bool:
        optional = self._check_optional(template_data)
        key_available = self._check_key_available(config, template_key)
        if key_available:
            return True
        if not key_available and optional:
            return False
        if not key_available and not optional:
            self.invalid_keys[template_key] = f"required key {template_key} is not in config file {config.config_path}"
            return False
        else:  # same branch as "if key_available". The else-statement is here to satisfy mypy.
            return True

    @staticmethod
    def _check_key_available(config: Config, key: str) -> bool:
        return key in config

    @staticmethod
    def _check_optional(template_data: dict) -> bool:
        return template_data.get("optional", False)
