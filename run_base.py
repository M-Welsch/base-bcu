import sys, os
import logging
from datetime import datetime
from pathlib import Path
import json

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)

from base.daemon.daemon import Daemon


def main():
    # TODO: Replace
    with open("base/config.json", "r") as file:
        logs_directory = json.load(file)["Logging"]["logs_directory"]

    logging.basicConfig(
        filename=Path(logs_directory)/datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log'),
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(name)s: %(message)s',
        datefmt='%m.%d.%Y %H:%M:%S'
    )
    Daemon()


if __name__ == '__main__':
    main()
