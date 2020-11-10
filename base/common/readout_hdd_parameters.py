import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

import json
from base.common.utils import run_external_command_as_generator_shell


def readout_parameters_of_all_hdds():
	# returns a dictionary with device identifier as key and corresponding parameters as value (in another dictionary)
	interim_dictionary = {}
	for sd_device in find_all_sd_devices():
		interim_dictionary[sd_device] = readout_hdd_parameters(sd_device)
	hdd_parameter_set = str(interim_dictionary).replace("'",'"')
	return hdd_parameter_set 


def readout_hdd_parameters(sd_device):
	#Todo: take a device identifier like sda as parameter
	model_number = "hdparm did not respond anything that would overwrite this string for model number"
	serial_number = "hdparm did not respond anything that would overwrite this string for serial number"
	device_size = "hdparm did not respond anything that would overwrite this string for device size"
	for line in run_external_command_as_generator_shell("sudo hdparm -I /dev/{}".format(sd_device)):
		line = str(line)
		try:
			model_number = extract_model_number(line)
		except:
			pass

		try:
			serial_number = extract_serial_number(line)
		except:
			pass

		try:
			device_size = extract_device_size(line)
		except:
			pass

	return dictionary_from_parameters(model_number, serial_number, device_size)


def dictionary_from_parameters(model_number, serial_number, device_size):
	hdd_parameters = {"Model Number" : model_number,
						  "Serial Number" : serial_number,
						  "device size with M = 1000*1000" : device_size}
	return hdd_parameters



def find_all_sd_devices():
	all_sd_devices = []
	for line in run_external_command_as_generator_shell("ls /dev | grep sd."):
		line = line[0:3]#.decode("utf-8")
		if not line in all_sd_devices:
			all_sd_devices.append(line)
	return all_sd_devices



def extract_model_number(line):
	return extract_value_from_line(line, "Model Number")


def extract_serial_number(line):
	return extract_value_from_line(line, "Serial Number")

def extract_device_size(line):
	return extract_value_from_line(line, "device size with M = 1000*1000")


def extract_value_from_line(line, key):
	index_found = line.find(key)
	if not index_found == -1:
		value = line[index_found + len(key) + 1:-3].strip()
	value.encode('ascii',errors='ignore')
	return value


if __name__ == "__main__":
	print(json.loads(readout_parameters_of_all_hdds()))