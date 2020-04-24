import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from base.hwctrl.hwctrl import HWCTRL

class Stepper_Tester():
	def test_docking():
		_hardware_control.get_hw_revision()
		# _hardware_control.dock()


if __name__ == "__main__":
	path_to_module = "/home/maxi"
	sys.path.append(path_to_module)
	_config = Config("base/config.json")
	_scheduler = BaseScheduler()
	_logger = Logger(_config.logs_directory)
	._hardware_control = HWCTRL(_config.hwctrl_config, _logger)
	ST = Stepper_Tester()