import numpy as np
import matplotlib.pyplot as plt


def read_table(filename):
	table = []
	with open(filename,"r") as measurements:
		for line in measurements.read().split('\n'):
			if not line:
				continue
			x,y = line.split(',')
			table.append([float(x),float(y.strip())])
	return table

table_measurements = read_table("table_adc_vs_measurement.csv")
table_approx_least_squares = read_table("table_adc_vs_measurement_appr.csv")
table_approx_least_m = read_table("table_adc_vs_measurement_appr_m.csv")
print(table_measurements)

plt.figure(num=None, figsize=(10, 6))
plt.xlabel('ADC readout [digits]')
plt.ylabel('Current [mA]')

plt.plot(table_measurements)
plt.show()