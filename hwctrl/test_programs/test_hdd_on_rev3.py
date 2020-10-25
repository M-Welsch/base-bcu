import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from base.hwctrl.hwctrl import HWCTRL
from base.common.base_logging import Logger
from base.common.config import Config
from time import sleep

class HDD_PWR_Tester():
	def __init__(self, hwctrl):
		self._hwctrl = hwctrl

	def test_pwr_on_off(self):
		self._hwctrl.hdd_power_on()
		sleep(2)
		#self._hwctrl.hdd_power_off()

if __name__ == "__main__":
	with_hwctrl = False
	if with_hwctrl:
		path_to_module = "/home/maxi"
		sys.path.append(path_to_module)
		_config = Config("/home/maxi/base/config.json")
		_logger = Logger("/home/maxi/base/log")
		_hwctrl = HWCTRL(_config.config_hwctrl, _logger)
		HddPT = HDD_PWR_Tester(_hwctrl)
		HddPT.test_pwr_on_off()
	else:
		import RPi.GPIO as GPIO
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(7, GPIO.OUT) #on
		GPIO.setup(18, GPIO.OUT) #off
		GPIO.output(7, GPIO.HIGH)
		sleep(0.01)
		GPIO.output(7, GPIO.LOW)
		GPIO.cleanup()


