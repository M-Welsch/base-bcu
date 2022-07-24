import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Type, Union

from base.common.config import Config


def patch_config(class_: Type, config_content: Dict[str, Any], read_only: bool = True) -> None:
    sys.modules[class_.__module__].get_config = lambda _: Config(config_content, read_only=read_only)  # type: ignore


def patch_multiple_configs(class_: Type, config_content: Dict[str, Dict[str, Any]]) -> None:
    def make_substitute_config(file_name: str) -> Config:
        config = Config(config_content[file_name])
        config["reload"] = lambda: None
        return config

    sys.modules[class_.__module__].get_config = lambda file_name: make_substitute_config(file_name)  # type: ignore


def next_backup_timestamp(seconds_to_next_backup: int) -> Dict[str, Union[str, int]]:
    next_bu = datetime.now() + timedelta(seconds=seconds_to_next_backup)
    return {"backup_interval": "days", "hour": next_bu.hour, "minute": next_bu.minute, "second": next_bu.second}
