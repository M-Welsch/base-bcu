import os
import sys
from pathlib import Path

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
@click.argument("log_dir", type=click.Path(), default=Path(__file__).parent / "log", required=False)
def main(mocked: bool, config_dir: Path, log_dir: Path) -> None:
    """BaSe Firmware"""
    setup_logger(log_dir)
    setup_config(config_dir)

    from base.base_application import BaSeApplication

    app = BaSeApplication()
    app.start()


if __name__ == "__main__":
    main()
