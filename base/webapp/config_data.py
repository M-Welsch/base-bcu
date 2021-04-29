import json
from pathlib import Path

from base.common.config import Config


def get_config_data():
    def json_content(path):
        with open(path, "r") as jf:
            return json.load(jf)

    return json.dumps({file.stem: json_content(file) for file in Path(Config.base_path).glob("*.json")})
