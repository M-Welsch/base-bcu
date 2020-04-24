import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from base.hwctrl.hwctrl import HWCTRL
from base.common.base_logging import Logger
from base.common.config import Config

class Stepper_Tester():
	def test_docking(self):
		_hardware_control.dock()
		_hardware_control.undock()


if __name__ == "__main__":
	path_to_module = "/home/maxi"
	sys.path.append(path_to_module)
	_config = Config("/home/maxi/base/config.json")
	_logger = Logger("/home/maxi/base/log")
	_hardware_control = HWCTRL(_config.hwctrl_config, _logger)
	ST = Stepper_Tester()
	ST.test_docking()
