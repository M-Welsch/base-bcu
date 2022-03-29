import os
import sys
from pathlib import Path

import click

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)


@click.command()
@click.option("--dock", "-d", help="dock backup hdd", is_flag=True, default=False)
@click.option("--undock", "-u", help="undock backup hdd", is_flag=True, default=False)
@click.option("--power", "-p", help="power backup hdd", is_flag=True, default=False)
@click.option("--unpower", "-r", help="unpower backup hdd", is_flag=True, default=False)
@click.option(
    "--open_sbu_channel",
    "-c",
    help="set communication path to communication (not programming) and enable BCU to receive messages",
    is_flag=True,
    default=False,
)
@click.option(
    "--close_sbu_channel",
    "-v",
    help="set communication path to programming and disable BCU to receive messages",
    is_flag=True,
    default=False,
)
def control_hardware(
    dock: bool,
    undock: bool,
    power: bool,
    unpower: bool,
    mount: bool,
    unmount: bool,
    open_sbu_channel: bool,
    close_sbu_channel: bool,
) -> None:
    cfg_path = Path("/home/base/base-bcu/base/config/")
    setup_logger(cfg_path)
    from base.common.config import BoundConfig

    setup_config(cfg_path)

    from base.hardware.drive import Drive
    from base.hardware.mechanics import Mechanics
    from base.hardware.power import Power

    power_unit = Power()
    mechanics = Mechanics()
    drive = Drive()

    if dock:
        print("docking")
        mechanics.dock()
    if power:
        print("power")
        power_unit.hdd_power_on()
    if mount:
        print("mounting")
        drive.mount()
    if unmount:
        print("unmounting")
        drive.unmount()
    if unpower:
        print("unpower")
        power_unit.hdd_power_off()
    if undock:
        print("undocking. Properly")
        mechanics.undock()
    if open_sbu_channel:
        print("Opening Channel")
        power_unit._pin_interface.set_sbu_serial_path_to_communication()
        power_unit._pin_interface.enable_receiving_messages_from_sbu()
    if close_sbu_channel:
        print("Closing Channel")
        power_unit._pin_interface.set_sbu_serial_path_to_sbu_fw_update()
        power_unit._pin_interface.disable_receiving_messages_from_sbu()


def setup_config(config_path: Path) -> None:
    from base.common.config import BoundConfig

    BoundConfig.set_config_base_path(config_path)


def setup_logger(config_path: Path) -> None:
    from base.common.logger import LoggerFactory

    LoggerFactory(config_path, "BaSe", development_mode=True)


if __name__ == "__main__":
    control_hardware()
