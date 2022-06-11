import os
import sys
from pathlib import Path
from typing import Any, Type

import click


def setup_config(config_path: Path) -> None:
    from base.common.config import BoundConfig

    BoundConfig.set_config_base_path(config_path)


def setup_logger(logs_directory: Path) -> None:
    from base.common.logger import LoggerFactory

    LoggerFactory(logs_directory, "BaSe", development_mode=True)


@click.command()
@click.argument("config-dir", type=click.Path(), default=Path(__file__).parent / "config", required=False)
@click.argument("log-dir", type=click.Path(), default=Path(__file__).parent / "log", required=False)
@click.option("--no-shutdown", is_flag=True, help="Do not shutdown after termination. For testing.")
def main(config_dir: Path, log_dir: Path, no_shutdown: bool) -> None:
    """BaSe Firmware"""
    setup_logger(log_dir)
    setup_config(config_dir)

    from base.base_application import BaSeApplication

    app = BaSeApplication()
    app.start()

    if no_shutdown:
        print("shutdown command overridden. Staying awake.")
    else:
        os.system("shutdown -h now")


if __name__ == "__main__":
    main()
