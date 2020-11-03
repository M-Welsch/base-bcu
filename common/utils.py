import os
from time import sleep
from subprocess import run, Popen, PIPE, STDOUT
import socket
from base.common.exceptions import *


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


def wait_for_device_file(device_file_path, timeout):
	for counter in range(timeout):
		if device_file_present(device_file_path):
			return True
		sleep(1)
	return False


def device_file_present(device_file_path):
	return os.path.exists(device_file_path)


def run_external_command(command, success_msg, error_msg):
	cp = run(command, stdout=PIPE, stderr=PIPE)
	if cp.stderr:
		print(error_msg, cp.stderr)
		raise ExternalCommandError(cp.stderr)
	else:
		print(success_msg)


def run_external_command_as_generator(command):
	p = Popen(command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=STDOUT)
	return p.stdout


def run_external_command_as_generator_shell(command):
	p = Popen(command, bufsize=0, shell=True, universal_newlines=True, stdout=PIPE, stderr=STDOUT)
	return p.stdout


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


def check_path_end_slash_and_asterik(path_to_check):
	if path_to_check.endswith('/*'):
		pass
	elif path_to_check.endswith('/'):
		path_to_check += '*'
	else:
		path_to_check += '/*'
	return path_to_check


def check_path_end_slash(path_to_check):
	if not path_to_check.endswith('/'):
		path_to_check += '/'
	return path_to_check


def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		# doesn't even have to be reachable
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except Exception:
		IP = '127.0.0.1'
	finally:
		s.close()
	return IP


def get_sbu_fw_uploads_folder():
	return "{}/sbu_interface/sbu_fw_uploads".format(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def shutdown_bcu():
	os.system("shutdown -h now")


def network_available():
	ip_address = get_ip_address()
	return not ip_address == "127.0.0.1"
