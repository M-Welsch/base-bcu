import sys, os
import numpy as np

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
		self.save_result(current_values_adc, current_values_multimeter, "table_adc_vs_measurement.csv")

		lin_params = self.calculate_linear_parameters_by_least_squares(current_values_multimeter, current_values_adc)
		appr_x, appr_y = self.compute_approximated_values(lin_params)
		self.save_result(appr_x, appr_y, "table_adc_vs_measurement_appr.csv")

		m = self.calculate_m_as_mean(current_values_multimeter, current_values_adc)
		appr_x, appr_y = self.compute_approximated_values(m)
		self.save_result(appr_x, appr_y, "table_adc_vs_measurement_appr_m.csv")


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

	def calculate_m_as_mean(self, current_values_multimeter, current_values_adc):
		m = []
		for current_value_multimeter, current_value_adc in zip(current_values_multimeter, current_values_adc):
			m.append(current_value_multimeter / current_value_adc)
		return np.mean(m)

	def calculate_linear_parameters_by_least_squares(self, current_values_multimeter, current_values_adc):
		list_A = []
		vector_y = []

		for current_value_adc in current_values_adc:
			list_A.append([current_value_adc, 1])
		# print(list_A)
		matrix_A = np.array(list_A)
		vector_y.extend(np.array(current_values_multimeter))
		matrix_At = np.transpose(matrix_A)
		# print(vector_y)

		return list(np.linalg.inv(matrix_At.dot(matrix_A)).dot(matrix_At).dot(vector_y))

	def save_result(self, x_data, y_data, filename):
		# print("x_data: {}, y_data {}".format(x_data, y_data))
		with open(filename, "w") as f:
			for x,y in zip(x_data, y_data):
				# print("x_data {}, y_data {}\n".format(x_data[index], y_data[index]))
				f.write("{}, {}\n".format(x,y))
			f.close()

	def compute_approximated_values(self, lin_params):
		if not type(lin_params) == list:
			lin_params = [lin_params, 0]
		print("lin_params: m = {}, t = {}".format(lin_params[0], lin_params[1]))
		x = list(range(1000))
		y = []
		for x_instance in x:
			y.append(lin_params[0] * x_instance + lin_params[1])
		return x,y

if __name__ == '__main__':
	CSC = Current_Sensor_Calibrator()
	CSC.calibrate_current_sensor()