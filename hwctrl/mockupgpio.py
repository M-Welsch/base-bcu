from base.hwctrl.hw_definitions import *

class GPIO():
	def setmode(mode):
		print("GPIO Mockup: Pretending to setup according to {}".format(mode))

	def setup(pin, direction, pull_up_down=None):
		print("GPIO Mockup: Setting Direction of pin {} to {}".format(pin, direction))
		if pull_up_down:
			print("enabling Pullup")

	def input(pin):
		if pin in [21, 23]:
			# simulated a non-pressed button
			return 1
		print("GPIO Mockup: Pin {} Sensing LOW".format(pin))
		return 0

	def output(pin, state):
		if not pin == 24:
			# pin 24 is the heartbeat-pin which is toggled with 100Hz
			print("GPIO Mockup: Setting output on pin {} to {}".format(pin, state))


	BOARD = "Physical Pinout"
	OUT = "Output"
	IN = "Input"
	PUD_UP = "Pullup"
	LOW = 0
	HIGH = 1