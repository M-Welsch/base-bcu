import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from time import sleep

class Stepper_Tester():
	def test_docking(self):
		_hardware_control.dock()
		sleep(1)
		_hardware_control.undock()

def Stepper_Tester_wo_hwctrl():
	import RPi.GPIO as GPIO
	stepper_reset = 12
	stepper_step = 15
	stepper_dir = 19
	endswitch_undocked = 11
	endswitch_docked = 13
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(stepper_reset, GPIO.OUT)
	GPIO.setup(stepper_step, GPIO.OUT)
	GPIO.setup(stepper_dir, GPIO.OUT)
	GPIO.setup(endswitch_docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(endswitch_undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	GPIO.output(stepper_step, GPIO.LOW)
	GPIO.output(stepper_reset, GPIO.HIGH)
	GPIO.output(stepper_dir, GPIO.LOW)

	# dock
	while GPIO.input(endswitch_undocked):
		GPIO.output(stepper_step, GPIO.HIGH)
		sleep(0.0005)
		GPIO.output(stepper_step, GPIO.LOW)
		sleep(0.0005)

	GPIO.output(stepper_reset, GPIO.LOW)
	GPIO.cleanup()

if __name__ == "__main__":
	# path_to_module = "/home/maxi"
	# sys.path.append(path_to_module)
	# _config = Config("/home/maxi/base/config.json")
	# _hardware_control = HWCTRL.global_instance(_config.hwctrl_config)
	# ST = Stepper_Tester()
	# ST.test_docking()
	Stepper_Tester_wo_hwctrl()
