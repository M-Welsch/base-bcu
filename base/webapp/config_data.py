import json
from pathlib import Path
from typing import Any

from base.common.config import Config
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


def get_config_data() -> str:
    def json_content(path: Path) -> Any:
        with open(path, "r") as jf:
            return json.load(jf)

    return json.dumps({file.stem: json_content(file) for file in Path(Config.base_path).glob("*.json")})


def update_config_data(new_cfg_s: str) -> None:
    try:
        new_cfg = json.loads(new_cfg_s)
    except json.JSONDecodeError as e:
        LOG.warning(f"config from webapp is invalid: {e}")
    else:
        for file, new_content in new_cfg.items():
            update_config_file(file, new_content)


def update_config_file(file: str, new_content: Any) -> None:
    try:
        config_filename = Path(Config.base_path) / f"{file}.json"
        with open(config_filename, "r") as config_file:
            config: dict = json.load(config_file)
        config.update(new_content)
        with open(config_filename, "w") as config_file:
            json.dump(config, config_file, indent=4)
    except FileNotFoundError as e:
        LOG.warning(f"config file to update doesn't exist: {e}")
    except json.JSONDecodeError:
        LOG.warning(f"config is invalid: {file}, {new_content}")
