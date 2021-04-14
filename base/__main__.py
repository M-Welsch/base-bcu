import sys
import os
from pathlib import Path

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# TODO: Fix this somehow...
# print(path_to_module)
# print(os.getcwd())
# print('\n'.join(sys.path))
sys.path.append(path_to_module)


def setup_config():
	from base.common.config import Config
	Config.set_config_base_path(Path("/home/base/python.base/base/config/"))


def setup_logger():
	from base.common.logger import LoggerFactory
	LoggerFactory.setup("BaSe", development_mode=True)


def main():
	from base.base_application import BaSeApplication
	app = BaSeApplication()
	app.start()


if __name__ == '__main__':
	setup_config()
	setup_logger()
	main()
