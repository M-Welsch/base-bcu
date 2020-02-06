import sys, os
import numpy as np
import matplotlib.pyplot as plt

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

from base.hwctrl.hw_definitions import *
from base.hwctrl.current_measurement import Current_Measurement
from base.hwctrl.lcd import *

class Current_Sensor_Calibrator():
	def __init__(self):
		self.current_values_multimeter = []
		self.pin_interface = PinInterface(100)
		self.lin_params = []

	def calibrate_current_sensor(self):
		current_values_multimeter, current_values_adc = self.get_current_values()
		self.calculate_linear_parameters(current_values_multimeter, current_values_adc)
		print(self.lin_params)
		self.output_result()

	def get_current_values(self):
		current_values_multimeter = []
		current_values_adc = []
		current_value_multimeter = 1
		while current_value_multimeter:

			self.activate_current_flow()
			current_value_multimeter = self.get_current_value_from_user_input_or_quit()
			if not current_value_multimeter:
				break
			current_value_from_adc = self.get_current_value_from_adc(10,0.1)

			current_values_multimeter.append(current_value_multimeter)
			current_values_adc.append(current_value_from_adc)

			self.deactivate_current_flow()
			if not self.ask_user_for_additional_measurement():
				break

		return current_values_multimeter, current_values_adc

	def ask_user_for_additional_measurement(self):
		user_input = (input("new measurement? [Y/n]: ") or "Y")
		if user_input.lower() == "n":
			user_input = False
		return user_input

	def get_current_value_from_user_input_or_quit(self):
		user_input = input("Enter current value from multimeter in mA (or 'q' to quit): ")
		if user_input == "q":
			user_input = False
		return int(user_input)

	def activate_current_flow(self):
		self.pin_interface.activate_hdd_pin()

	def deactivate_current_flow(self):
		self.pin_interface.deactivate_hdd_pin()

	def get_current_value_from_adc(self, iterations, interval):
		self.initiate_current_measurement()

		current_measurements = []
		iteration_index = 0
		while iteration_index < iterations:
			meas = self.cur_meas.current
			current_measurements.append(meas)
			print("Doing iteration {}, measuring {}".format(iteration_index, meas))
			sleep(interval)
			iteration_index += 1

		self.terminate_current_measurement()
		return np.mean(current_measurements)

	def terminate_current_measurement(self):
		self.cur_meas.terminate()

	def initiate_current_measurement(self):
		self.cur_meas = Current_Measurement(0.05)
		self.cur_meas.start()

	def calculate_linear_parameters(self, current_values_multimeter, current_values_adc):
		list_A = []
		for current_value_adc in current_values_adc:
			list_A.append([current_value_adc, 1])
		print(list_A)
		matrix_A = np.array(list_A)
		vector_y = np.array(current_values_multimeter)
		matrix_At = np.transpose(matrix_A)
		print(vector_y)

		self.lin_params = list(np.linalg.inv(matrix_At.dot(matrix_A)).dot(matrix_At).dot(vector_y))

	def output_result(self):
		x = list(range(1000))
		fitted_y = self.compute_approximated_values(x)
		plt.figure(num=None, figsize=(10, 6))
		plt.xlabel('Rounds')
		plt.ylabel('Points')
		plt.plot(x, fitted_y, label='fitted', color='red')
		plot.savefig("calib.png")

	def compute_approximated_values(self, x):
		y = []
		for x_instance in x:
			y.append(self.lin_params[0] * x_instance + self.lin_params[1])
		return y

if __name__ == '__main__':
	CSC = Current_Sensor_Calibrator()
	CSC.calibrate_current_sensor()