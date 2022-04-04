import os
import sys
from pathlib import Path
from typing import Any, Type

import click

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# TODO: Fix this somehow...
# print(path_to_module)
# print(os.getcwd())
# print('\n'.join(sys.path))
sys.path.append(path_to_module)


def setup_config(config_path: Path) -> None:
    from base.common.config import BoundConfig

    BoundConfig.set_config_base_path(config_path)


def setup_logger(logs_directory: Path) -> None:
    from base.common.logger import LoggerFactory

    LoggerFactory(logs_directory, "BaSe", development_mode=True)


@click.command()
@click.option("--mocked", is_flag=True, help="Mock hardware to allow running on arbitrary machines")
@click.argument("config_dir", type=click.Path(), default=Path(__file__).parent / "config", required=False)
@click.argument("log_dir", type=click.Path(), default=Path(__file__).parent.parent / "log", required=False)
def main(mocked: bool, config_dir: Path, log_dir: Path) -> None:
    """BaSe Firmware"""
    setup_logger(log_dir)
    setup_config(config_dir)

    from base.base_application import BaSeApplication

    try:
        app = BaSeApplication()
        app.start()
    except Exception as e:
        write_email(e)
        raise e
    try:
        app.finalize_service()
    except Exception as e:
        raise e
    # os.system("shutdown -h now")  # TODO: os.system() is deprecated. Replace with subprocess.call().


def write_email(exception: Exception) -> Any:
    ...


if __name__ == "__main__":
    main()
