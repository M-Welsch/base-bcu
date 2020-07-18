import sys
from time import sleep
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from base.hwctrl.hw_definitions import *

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

class rev3b_bringup_test_suite():
	def __init__(self):
		self.display_brightness = 1
		self._pin_interface = PinInterface(self.display_brightness)
		self.testcases = ["test_endswitches", "test_pushbuttons", "test_stepper"]

	def run(self):
		Tester = None
		exitflag = False
		while not exitflag:
			user_choice = self.ask_user_for_testcase()
			if user_choice in ["q","Quit"]:
				exitflag = True

			if user_choice in ["0","test_endswitches"]:
				Tester = rev3b_endswitch_tester(self._pin_interface)

			if user_choice in ["2","test_stepper"]:
				Tester = rev3b_stepper_tester(self._pin_interface)

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