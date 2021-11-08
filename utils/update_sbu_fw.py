import os
import sys
from pathlib import Path

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)


def setup_config(config_path: Path) -> None:
    from base.common.config import BoundConfig

    BoundConfig.set_config_base_path(config_path)


def setup_logger(config_path: Path) -> None:
    from base.common.logger import LoggerFactory

    LoggerFactory(config_path, "BaSe", development_mode=True)


def main() -> None:
    from base.hardware.sbu.updater import SbuUpdater

    usbu = SbuUpdater()
    usbu.update()


if __name__ == "__main__":
    cfg_path = Path("/home/base/python.base/base/config/")
    setup_logger(cfg_path)
    setup_config(cfg_path)
    main()
