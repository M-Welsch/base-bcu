import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from base.common.utils import run_external_command_as_generator, wait_for_new_device_file

def readout_parameters_of_all_hdds():
	# returns a dictionary with device identifier as key and corresponding parameters as value (in another dictionary)
	hdd_parameter_set = "{"
	for sd_device in find_all_sd_devices():
		hdd_parameter_set += '"' + sd_device + '":' + readout_hdd_parameters(sd_device) + ','
	return hdd_parameter_set[:-1] + "}"

def readout_hdd_parameters(sd_device):
	#Todo: take a device identifier like sda as parameter
	model_number = "hdparm did not respond anything that would overwrite this string for model number"
	serial_number = "hdparm did not respond anything that would overwrite this string for serial number"
	for line in run_external_command_as_generator("sudo hdparm -I /dev/{}".format(sd_device)):
		line = str(line)
		try:
			model_number = extract_model_number(line)
		except:
			pass

		try:
			serial_number = extract_serial_number(line)
		except:
			pass

	return dictionary_from_parameters(model_number, serial_number)


def dictionary_from_parameters(model_number, serial_number):
	return '{"model_number":"' + model_number + '", "serial_number":"' + serial_number + '"}'



def find_all_sd_devices():
	all_sd_devices = []
	for line in run_external_command_as_generator("ls /dev | grep sd."):
		line = line[0:3].decode("utf-8")
		if not line in all_sd_devices:
			all_sd_devices.append(line)
	return all_sd_devices



def extract_model_number(line):
	return extract_value_from_line(line, "Model Number")


def extract_serial_number(line):
	return extract_value_from_line(line, "Serial Number")


def extract_value_from_line(line, key):
	index_found = line.find(key)
	if not index_found == -1:
		value = line[index_found + len(key) + 1:-3].strip()
	return value


if __name__ == "__main__":
	print(readout_parameters_of_all_hdds())