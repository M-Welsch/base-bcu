import os
from time import time, sleep
from subprocess import run, Popen, PIPE, STDOUT

# deprecated
def wait_for_new_device_file(seconds):
	device_files_before = get_device_files()
	for i in range(seconds):
		sleep(1)
		device_files_after = get_device_files()
		if len(device_files_after) > len(device_files_before):
			return set(device_files_after).difference(set(device_files_before))
	raise RuntimeError(f"Device file for backup HDD didn't appear in time (after {seconds} seconds).")


def get_device_files():
	all_device_files = os.listdir("/dev/")
	return [f for f in all_device_files if f.startswith("sd")]


def wait_for_device_file(device_file, timeout):
	for counter in range(timeout):
		if device_file_present(device_file):
			return True
		sleep(1)
	return False


def device_file_present(device_file):
	return os.path.exists(device_file)


def run_external_command(command, success_msg, error_msg):
	cp = run(command, stdout=PIPE, stderr=PIPE)
	if cp.stderr:
		print(error_msg, cp.stderr)
		raise RuntimeError(error_msg, cp.stderr)
	else:
		print(success_msg)


def run_external_command_string_input(command):
	cp = run(command, shell=True, stdout=PIPE, stderr=STDOUT)
	return cp


def run_external_command_as_generator(command):
	p = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
	return iter(p.stdout.readline, b'')


def run_external_command_and_return_string(command):
	response = ""
	for line in run_external_command_as_generator(command):
		response += line.decode('utf-8') + '\n'
	return response


def run_external_command_as_generator_2(command):
	p = Popen(command, stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True)
	return p.stdout


def readout_hdd_parameters():
	#Todo: take a device identifier like sda as parameter
	model_number = "hdparm did not respond anything that would overwrite this string for model number"
	serial_number = "hdparm did not respond anything that would overwrite this string for serial number"
	for line in run_external_command_as_generator("sudo hdparm -I /dev/sda"):
		line = str(line)
		try:
			model_number = extract_model_number(line)
		except:
			pass

		try:
			serial_number = extract_serial_number(line)
		except:
			pass

	return [model_number, serial_number]


def extract_model_number(line):
	return extract_value_from_line(line, "Model Number")


def extract_serial_number(line):
	return extract_value_from_line(line, "Serial Number")


def extract_value_from_line(line, key):
	index_found = line.find(key)
	if not index_found == -1:
		value = line[index_found + len(key) + 1:-3].strip()
	return value


def status_quo_not_empty(status_quo):
	b = False
	for value in status_quo.values():
		b += or_up_values(value)
	return b

def or_up_values(value):
	b = False
	if type(value) == tuple:
		for entry in value:
			if entry == "False":
				entry = False
			b += bool(entry)
	else:
		b += bool(value)
	return b

def list_backups_by_age(bu_location):
	# lowest index is the oldest
	list_of_backups = []
	for file in os.listdir(bu_location):
		if file.startswith("backup"):
			list_of_backups.append(file)
	list_of_backups.sort()
	return list_of_backups

def get_oldest_backup():
	backups = list_backups_by_age()
	if backups:
		return backups[0]
	else:
		raise RuntimeError("'get_oldest_backup': no backup done yet!")

def get_sbc_fw_uploads_folder():
	return "{}/sbc_interface/sbc_fw_uploads".format(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))