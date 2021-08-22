import os
import sys
from pathlib import Path

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)

from base.common.config import Config
from base.hardware.sbu.sbu_updater import SbuUpdater


class UpdateSbu:
    def __init__(self) -> None:
        Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
        self._sbuu = SbuUpdater()

    def update(self) -> None:
        self._sbuu.update()


if __name__ == "__main__":
    usbu = UpdateSbu()
    usbu.update()
