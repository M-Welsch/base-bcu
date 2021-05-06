import json
from pathlib import Path

from base.common.config import Config
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


def get_config_data():
    def json_content(path):
        with open(path, "r") as jf:
            return json.load(jf)

    return json.dumps({file.stem: json_content(file) for file in Path(Config.base_path).glob("*.json")})


def update_config_data(new_cfg_s: str):
    new_cfg = {}
    try:
        new_cfg = json.loads(new_cfg_s)
    except json.JSONDecodeError as e:
        LOG.warning(f"config from webapp is invalid: {e}")
    for file, content in new_cfg.items():
        update_config_file(content, file)


def update_config_file(content, file):
    try:
        cfg_filename = Path(Config.base_path) / f"{file}.json"
        with open(cfg_filename, "r") as cfg_file:
            cfg: dict = json.load(cfg_file)
        cfg.update(content)
        with open(cfg_filename, "w") as cfg_file:
            json.dump(cfg, cfg_file, indent=4)
    except FileNotFoundError as e:
        LOG.warning(f"config file to update doesn't exist: {e}")
    except json.JSONDecodeError:
        LOG.warning(f"config is invalid: {file}, {content}")
