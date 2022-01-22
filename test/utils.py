import sys
from typing import Any, Dict, Type

from base.common.config import Config


def patch_config(class_: Type, config_content: Dict[str, Any]) -> None:
    sys.modules[class_.__module__].get_config = lambda _: Config(config_content)  # type: ignore


def patch_multiple_configs(class_: Type, config_content: Dict[str, Dict[str, Any]]) -> None:
    sys.modules[class_.__module__].get_config = lambda file_name: Config(config_content[file_name])  # type: ignore
