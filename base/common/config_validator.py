from __future__ import annotations

import json
import re
from pathlib import Path
from pydoc import locate
from types import TracebackType
from typing import Dict, Optional, Type

from base.common.config import BoundConfig, ConfigValidationError


class ConfigValidator:
    type_to_check = {"str": str, "pathlib.Path": str, "int": int, "bool": bool}
    validation_pipeline_map = {
        "str": ["_check_type_validity", "_check_regex"],
        "pathlib.Path": ["_check_type_validity", "_check_path_resolve"],
        "int": ["_check_type_validity", "_check_range"],
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

    def _check_type_validity(self, key: str, template_data: dict, config: BoundConfig) -> None:
        valid_type = locate(template_data["type"])
        if type(config[key]) is not self.type_to_check[template_data["type"]]:
            self.invalid_keys[key] = (
                f"Value of key '{key}' has invalid type {type(config[key])} "
                f"in config file {config.config_path}. Should be: {valid_type}"
            )

    def _check_regex(self, key: str, template_data: dict, config: BoundConfig) -> None:
        if not re.fullmatch(pattern=template_data["valid"], string=config[key]):
            self.invalid_keys[key] = (
                f"Value {config[key]} of key {key} in config file {config.config_path} "
                f"does not match the regex {template_data['valid']}"
            )

    def _check_range(self, key: str, template_data: dict, config: BoundConfig) -> None:
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

    def _check_path_resolve(self, key: str, template_data: dict, config: BoundConfig) -> None:
        try:
            Path(config[key]).resolve()
        except ValueError:
            self.invalid_keys[key] = (
                f"Value {config[key]} of key {key} in config file {config.config_path} " f"is not a valid path"
            )

    def validate(self, config_to_validate: BoundConfig) -> None:
        with open(config_to_validate.template_path, "r") as template_file:
            template = json.load(template_file)

        for template_key, template_data in template.items():
            if config_to_validate[template_key] or not template_data.get("optional", False):
                for step_name in self.validation_pipeline_map[template_data["type"]]:
                    step_func = getattr(self, step_name)
                    step_func(template_key, template_data, config_to_validate)
