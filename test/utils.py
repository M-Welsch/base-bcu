from typing import Type

from base.common.config import Config
import sys


def patch_config(class_: Type, config_content: dict) -> None:
    sys.modules[class_.__module__].get_config = lambda _: Config(config_content)  # type: ignore
