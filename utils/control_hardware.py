import os
import sys
from pathlib import Path
import click

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)


@click.command()
@click.option('--dock', '-d', help='dock backup hdd', is_flag=True, default=False)
@click.option('--undock', '-u', help='undock backup hdd', is_flag=True, default=False)
@click.option('--power', '-p', help='power backup hdd', is_flag=True, default=False)
@click.option('--unpower', '-r', help='unpower backup hdd', is_flag=True, default=False)
def control_hardware(dock, undock, power, unpower):
    cfg_path = Path("/home/base/python.base/base/config/")
    setup_logger(cfg_path)
    setup_config(cfg_path)

    from base.hardware.hardware import Hardware
    from base.logic.backup.backup_browser import BackupBrowser
    hardware = Hardware(backup_browser=BackupBrowser())

    if dock:
        print("docking")
        hardware.dock()
    if power:
        print("power")
        hardware.power()
    if unpower:
        print("unpower")
        hardware.unpower()
    if undock:
        print("undocking. Properly")
        hardware.undock()


def setup_config(config_path: Path) -> None:
    from base.common.config import Config

    Config.set_config_base_path(config_path)


def setup_logger(config_path: Path) -> None:
    from base.common.logger import LoggerFactory

    LoggerFactory(config_path, "BaSe", development_mode=True)


if __name__ == "__main__":
    control_hardware()
