import sys, os
import numpy as np
from collections import OrderedDict

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

from base.deprecated.hwctrl.hw_definitions import *
from base.deprecated.hwctrl import Current_Measurement


class Current_Sensor_Calibrator():
	def __init__(self):
		self.current_values_multimeter = []
		self.pin_interface = PinInterface(100)
		self.lin_params = []

	def calibrate_current_sensor(self):
		current_values = self.get_current_values()
		self.save_result(list(current_values.keys()), list(current_values.values()),
						 "table_adc_vs_measurement.csv")

		lin_params = self.calculate_linear_parameters_by_least_squares(current_values)
		appr_x, appr_y = self.compute_approximated_values(lin_params, current_values)
		self.save_result(appr_x, appr_y, "table_adc_vs_measurement_appr.csv")

		m = self.calculate_m_as_mean(current_values)
		appr_x, appr_y = self.compute_approximated_values(m, current_values)
		self.save_result(appr_x, appr_y, "table_adc_vs_measurement_appr_m.csv")


	def get_current_values(self):
		current_values = {}
		current_value_multimeter = 1
		while current_value_multimeter:

			self.activate_current_flow()
			current_value_multimeter = self.get_current_value_from_user_input_or_quit()
			if current_value_multimeter == "q":
				break
			else:
				current_value_multimeter = int(current_value_multimeter)
			current_value_from_adc = self.get_current_value_from_adc(10,0.1)

			current_values[current_value_from_adc] = current_value_multimeter

			self.deactivate_current_flow()
			if not self.ask_user_for_additional_measurement():
				break

		return OrderedDict(sorted(current_values.items()))

	def ask_user_for_additional_measurement(self):
		user_input = (input("new measurement? [Y/n]: ") or "Y")
		if user_input.lower() == "n":
			user_input = False
		return user_input

	def get_current_value_from_user_input_or_quit(self):
		return input("Enter current value from multimeter in mA (or 'q' to quit): ")

	def activate_current_flow(self):
		self.pin_interface.activate_hdd_pin()

	def deactivate_current_flow(self):
		self.pin_interface.deactivate_hdd_pin()

	def get_current_value_from_adc(self, iterations, interval):
		self.initiate_current_measurement()

		current_measurements = []
		iteration_index = 0
		while iteration_index < iterations:
			meas = self.cur_meas.adc_data
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

	def calculate_m_as_mean(self, current_values):
		m = []
		current_values_adc = list(current_values.keys())
		current_values_multimeter = list(current_values.values())
		for current_value_multimeter, current_value_adc in zip(current_values_multimeter, current_values_adc):
			m.append(current_value_multimeter / current_value_adc)
		return np.mean(m)

	def calculate_linear_parameters_by_least_squares(self, current_values):
		list_A = []
		vector_y = []
		current_values_adc = list(current_values.keys())
		current_values_multimeter = list(current_values.values())

		for current_value_adc in current_values_adc:
			list_A.append([current_value_adc, 1])
		# print(list_A)
		matrix_A = np.array(list_A)
		vector_y.extend(np.array(current_values_multimeter))
		matrix_At = np.transpose(matrix_A)
		# print(vector_y)

		return list(np.linalg.inv(matrix_At.dot(matrix_A)).dot(matrix_At).dot(vector_y))

	def save_result(self, x_data, y_data, filename):
		# x_data = list(data_dict.keys())
		# y_data = list(data_dict.values())

		with open(filename, "w") as f:
			self.write_data(x_data, f)
			f.write("\n")
			self.write_data(y_data, f)
			f.close()

	def write_data(self, data, file_handle):
		for point in data:
			file_handle.write("{}".format(point))
			if not point == data[-1]:
				file_handle.write(", ")

	def compute_approximated_values(self, lin_params, data_dict):

		x_values = list(data_dict.keys())
		if not type(lin_params) == list:
			lin_params = [lin_params, 0]
		print("lin_params: m = {}, t = {}".format(lin_params[0], lin_params[1]))
		y = []
		for x_instance in x_values:
			y.append(lin_params[0] * x_instance + lin_params[1])
		return x_values,y

if __name__ == '__main__':
	CSC = Current_Sensor_Calibrator()
	CSC.calibrate_current_sensor()