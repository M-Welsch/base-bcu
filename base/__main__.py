import sys
import os
from pathlib import Path

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# TODO: Fix this somehow...
# print(path_to_module)
# print(os.getcwd())
# print('\n'.join(sys.path))
sys.path.append(path_to_module)


def setup_config(config_path: Path):
	from base.common.config import Config
	Config.set_config_base_path(config_path)


def setup_logger(config_path: Path):
	from base.common.logger import LoggerFactory
	LoggerFactory(config_path, "BaSe", development_mode=True)


def main():
	from base.base_application import BaSeApplication
	app = BaSeApplication()
	app.start()


if __name__ == '__main__':
	cfg_path = Path("/home/base/python.base/base/config/")
	setup_logger(cfg_path)
	setup_config(cfg_path)
	main()
