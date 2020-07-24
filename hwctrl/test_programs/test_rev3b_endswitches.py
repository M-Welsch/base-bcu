import sys
from time import sleep
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from base.hwctrl.hw_definitions import *

def poll_endsw_status_periodically(pin_interface, period):
	while True:
		print_endswitches_status(pin_interface)
		sleep(period)

def print_endswitches_status(pin_interface):
	print("Endsw. Docked: {}, Endsw. Undocked: {}".format(pin_interface.docked_sensor_pin_high, pin_interface.undocked_sensor_pin_high))

if __name__ == "__main__":
	pin_interface = PinInterface(1)
	try:
		poll_endsw_status_periodically(pin_interface, 0.2)
	except KeyboardInterrupt:
		print("End.")

	pin_interface.cleanup
