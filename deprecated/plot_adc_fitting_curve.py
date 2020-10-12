import numpy as np
import matplotlib.pyplot as plt


def read_table(filename):
	x = []
	y = []
	table = []
	with open(filename,"r") as measurements:
		for line in measurements.read().split('\n'):
			if not line:
				continue
			table.append(line.split(','))
		measurements.close()
	x = np.asarray(table[0], dtype="float")
	y = np.asarray(table[1], dtype="float")
	return x, y

adc_vs_meas_x, adc_vs_meas_y = read_table("table_adc_vs_measurement.csv")
approx_ls_x, approx_ls_y = read_table("table_adc_vs_measurement_appr.csv")
approx_m_x, approx_m_y = read_table("table_adc_vs_measurement_appr_m.csv")
common_x = adc_vs_meas_x

plt.figure(num=None, figsize=(10, 6))
plt.title("Current Measurement and Linear Approxmations")
plt.xlabel("ADC readout [digits]")
plt.ylabel("Current [mA]")

plt.scatter(common_x, adc_vs_meas_y, label="measurement")
plt.plot(common_x, approx_ls_y, label="least squares approximation")
plt.plot(common_x, approx_m_y, label="m*x+t with t=0 and m as mean")

plt.legend(loc='best')

plt.show()