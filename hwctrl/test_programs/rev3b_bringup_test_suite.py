import sys
from time import sleep
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from base.hwctrl.hw_definitions import *
from base.hwctrl.hwctrl import *
from base.sbc_interface.sbc_communicator import *
from base.common.config import Config
from base.common.base_logging import Logger


class rev3b_endswitch_tester():
	def __init__(self, pin_interface):
		self._pin_interface = pin_interface

	def test(self):
		try:
			self.poll_endsw_status_periodically(0.2)
		except KeyboardInterrupt:
			print("End.")

	def poll_endsw_status_periodically(self, period):
		while True:
			self.print_endswitches_status()
			sleep(period)

	def print_endswitches_status(self):
		print("Endsw. Docked: {}, Endsw. Undocked: {} (End w. Ctrl+C)".format(self._pin_interface.docked_sensor_pin_high, self._pin_interface.undocked_sensor_pin_high))

class rev3b_pushbutton_tester():
	def __init__(self, pin_interface):
		self._pin_interface = pin_interface

	def test(self):
		print("The Pushbuttons can only be read if the SBC has its internal pullups on the button signals activated!")
		try:
			self.poll_button_status_periodically(0.2)
		except KeyboardInterrupt:
			print("End.")	

	def	poll_button_status_periodically(self, period):
		while True:
			self.print_endswitches_status()
			sleep(period)		

	def print_endswitches_status(self):
		print("Button 0: {}, Button 1: {} (End w. Ctrl+C)".format(self._pin_interface.button_0_pin_high, self._pin_interface.button_1_pin_high))

class rev3b_stepper_tester():
	def __init__(self, pin_interface):
		self._pin_interface = pin_interface

	def test(self):
		if self.warn_user_and_ask_whether_to_continue():
			self.active_stepper_driver()
			self.move_towards_docking()
			self.move_towards_undocking()
			self.deactivate_stepper_driver()
		else:
			print("Stepper Tester: aborting ...")

	def warn_user_and_ask_whether_to_continue(self):
		user_choice = input("Stepper Tester: Warning. This test moves the stepper. However it doesn't care about the endswitches! Continue [y/N]")
		if user_choice not in ["y", "Y", "Yes"]:
			return False
		else:
			return True

	def active_stepper_driver(self):
		self._pin_interface.stepper_driver_on()

	def move_towards_docking(self):
		print("Stepper Tester: Moving towords Dock Position")
		self._pin_interface.stepper_direction_docking()
		for i in range(1000):
			self._pin_interface.stepper_step()

	def move_towards_undocking(self):
		print("Stepper Tester: Moving towords Undock Position")
		self._pin_interface.stepper_direction_undocking()
		for i in range(1000):
			self._pin_interface.stepper_step()

	def deactivate_stepper_driver(self):
		self._pin_interface.stepper_driver_off()

class rev3b_serial_receive_tester():
	def __init__(self):
		hwctrl = self._init_hwctrl()
		self._SBCC = self._init_SBC_Communicator(hwctrl)

	def test(self):
		print("This test only print outs the Heartbeat Count sent by the SBC")
		try:
			self._writeout_from_sbc_queue_periodically(0.2)
		except KeyboardInterrupt:
			self._SBCC.terminate()
			print("End.")		

	def _init_hwctrl(self):
		config = Config("/home/maxi/base/config.json")
		logger = Logger("/home/maxi/base/log")
		return HWCTRL(config.hwctrl_config, logger)

	def _init_SBC_Communicator(self, hwctrl):
		self._from_SBC_queue = []
		self._to_SBC_queue = []
		SBCC = SBC_Communicator(hwctrl, self._to_SBC_queue, self._from_SBC_queue)
		SBCC.start()
		return SBCC

	def _writeout_from_sbc_queue_periodically(self, period):
		while True:
			while self._from_SBC_queue:
				print(self._from_SBC_queue.pop())
			sleep(period)

class rev3b_bringup_test_suite():
	def __init__(self):
		self.display_brightness = 1
		self._pin_interface = PinInterface(self.display_brightness)
		self.testcases = ["test_endswitches", "test_pushbuttons", "test_stepper", "test_SBC_heartbear_receive"]

	def run(self):
		Tester = None
		exitflag = False
		while not exitflag:
			user_choice = self.ask_user_for_testcase()
			if user_choice in ["q","Quit"]:
				exitflag = True

			if user_choice in ["0","test_endswitches"]:
				Tester = rev3b_endswitch_tester(self._pin_interface)

			if user_choice in ["1","test_pushbuttons"]:
				Tester = rev3b_pushbutton_tester(self._pin_interface)

			if user_choice in ["2","test_stepper"]:
				Tester = rev3b_stepper_tester(self._pin_interface)

			if user_choice in ["3", "test_SBC_heartbear_receive"]:
				Tester = rev3b_serial_receive_tester()

			if(Tester):
				Tester.test()
				Tester = None

		self._pin_interface.cleanup


	def ask_user_for_testcase(self):
		print("Choose a testcase by number:\n{}".format(self.list_of_testcases()))
		choice = input("Choose wisely: ")
		if choice in self.valid_choices():
			return choice
		else:
			# ask again
			print("Please make a valid choice. {} is invalid.".format(choice))
			self.ask_user_for_testcase()

	def list_of_testcases(self):
		list_of_testcases = ""
		testcase_index = 0
		for testcase in self.testcases:
			line = "({}) {}".format(testcase_index, testcase)
			list_of_testcases += line + '\n'
			testcase_index += 1
		list_of_testcases += "(q) Quit"
		return list_of_testcases

	def valid_choices(self):
		valid_choices = ['q']
		for choice in range(0,len(self.testcases)):
			valid_choices.extend(str(choice))
		return valid_choices

if __name__ == "__main__":
	print("""Welcome to the BaSe rev3b Hardware Bringup Test Suite.
This program enables you to test all BaSe specific hardware components.""")
	Suite = rev3b_bringup_test_suite()
	Suite.run()