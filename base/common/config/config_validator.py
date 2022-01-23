from __future__ import annotations

import json
import re
from pathlib import Path
from pydoc import locate
from types import TracebackType
from typing import Callable, Dict, List, Optional, Type

from base.common.config.unbound import Config
from base.common.exceptions import ConfigValidationError


class ConfigValidator:
    type_to_check = {
        "str": str,
        "pathlib.Path": str,
        "int": int,
        "float": float,
        "bool": bool,
        "dict": dict,
        "list": list,
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
        if not re.fullmatch(pattern=template_data["regex"], string=config[key]):
            self.invalid_keys[key] = (
                f"Value {config[key]} of key {key} in config file {config.config_path} "
                f"does not match the regex {template_data['regex']}"
            )

    def _check_range(self, key: str, template_data: dict, config: Config) -> None:
        minimum = template_data["range"]["min"]
        maximum = template_data["range"]["max"]
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
            self.invalid_keys[
                key
            ] = f"Value {config[key]} of key {key} in config file {config.config_path} is not a valid path"

    def _check_options(self, key: str, template_data: dict, config: Config) -> None:
        options = template_data["options"]
        if not config[key] in options:
            self.invalid_keys[
                key
            ] = f"Value {config[key]} of key {key} in config file {config.config_path} is not one of {options}"

    def _check_dict(self, key: str, template_data: dict, config: Config) -> None:
        """create a new config object from the dict and run the validation process"""
        sub_config = Config(config[key])
        sub_template = template_data[key]
        self._validate_items(template=sub_template, config=sub_config)

    def _check_ip(self, key: str, template_data: dict, config: Config) -> None:
        template_data[
            "regex"
        ] = r"(\\b25[0-5]|\\b2[0-4][0-9]|\\b[01]?[0-9][0-9]?)(\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"
        self._check_regex(key, template_data, config)

    def _check_linux_user(self, key: str, template_data: dict, config: Config) -> None:
        template_data["regex"] = r"^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\\$)$"
        self._check_regex(key, template_data, config)

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

    def _validate_item(self, config: Config, template_key: str, template_data: dict) -> None:
        if self._check_validation_required(config, template_key, template_data):
            pipeline = self.infer_validation_steps(template_data)
            for step_func in pipeline:
                step_func(template_key, template_data, config)

    def infer_validation_steps(self, template_data: dict) -> List[Callable]:
        steps = []
        if "type" in template_data:
            steps.append(self._check_type_validity)
            if template_data["type"] == "pathlib.Path":
                steps.append(self._check_path_resolve)
            if template_data["type"] == "dict":
                steps.append(self._check_dict)
        if "characteristic" in template_data:
            if template_data["characteristic"] == "ip":
                steps.append(self._check_ip)
            if template_data["characteristic"] == "linux_user":
                steps.append(self._check_linux_user)
        if "regex" in template_data:
            steps.append(self._check_regex)
        if "range" in template_data:
            steps.append(self._check_range)
        if "options" in template_data:
            steps.append(self._check_options)
        return steps

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
