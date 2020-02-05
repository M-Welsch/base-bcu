import sys, os
import numpy as np

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

from base.hwctrl.hw_definitions import *
from base.hwctrl.current_measurement import Current_Measurement
from base.hwctrl.lcd import *

class Current_Sensor_Calibrator():
	def __init__(self):
		self.current_values = []
		self.resistor_values = []
		self.pin_interface = PinInterface()

	def calibrate_current_sensor(self):
		self.get_resistor_and_current_values()
		self.calculate_linear_parameters()
		self.output_result()

	def get_resistor_and_current_values(self):
		resistor_value = 1
		finished = False
		while resistor_value:
			resistor_value = self.get_resistor_value_as_user_input()
			current_value = self.get_current_value_as_measurement(10,1)
			self.resistor_values.append(resistor_value)

	def get_resistor_value_as_user_input(self):
		user_input = input("Connect Resistor to Pin 1 and 2 of Sub-D. Enter Resistor Value in Ohms or 'q' to exit: ")
		if user_input == "q":
			user_input = False
		return user_input

	def get_current_value_as_measurement(self, iterations, interval):
		self.initiate_current_measurement()
		pin_interface.activate_hdd_pin()

		current_measurements = []
		while iteration_index < iterations:
			meas = self.cur_meas.current
			current_measurements.append(meas)
			print("Doing iteration {}, measuring {}".format(iteration_index, meas))
			current_from_multimeter = 
			sleep(interval)
		return np.mean(current_measurements)

	def get_current_value_as_user_input(self):
		return input("Enter Current Value from Multimeter in mA: ")

	def initiate_current_measurement(self):
		self.cur_meas = Current_Measurement(0.1)
		self.cur_meas.start()

	def calculate_linear_parameters(self):
		pass

	def output_result(self):
		pass

if __name__ == '__main__':
	CSC = Current_Sensor_Calibrator()
	CSC.calibrate_current_sensor()