import os
from time import time, sleep
from subprocess import run, Popen, PIPE, STDOUT

from paramiko import SSHClient

# depreached
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


def run_external_command_as_generator(command):
	p = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
	return iter(p.stdout.readline, b'')
	
def run_external_command_as_generator_2(command):
	p = Popen(command, stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True)
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


class SSHInterface:
	def __init__(self, host, user):
		self._client = SSHClient()
		self._client.load_system_host_keys()
		self._client.connect(host, username=user)

	def __enter__(self):
		return self

	def __exit__(self, *args):
		self._client.close()

	def run(self, command):
		response_stdout = ""
		response_stderr = ""
		stdin, stdout, stderr = self._client.exec_command(command)
		stderr_lines = "\n".join([line.strip() for line in stderr])
		if stderr_lines:
			response_stderr = "".join([line for line in stderr])
			if response_stderr:
				print("Unraised Error in 'SSHInterface.run': {}".format(response_stderr))
		else:
			response_stdout = "".join([line for line in stdout])
		return response_stdout


	def run_and_raise(self, command):
		stdin, stdout, stderr = self._client.exec_command(command)
		stderr_lines = "\n".join([line.strip() for line in stderr])
		if stderr_lines:
			raise RuntimeError(stderr_lines)
		else:
			return "".join([line for line in stdout])


def run_commands_over_ssh(host, user, commands):
	streams = {"stdout": [], "stderr": []}
	with SSHClient() as client:
		client.load_system_host_keys()
		client.connect(host, username=user)
		for command in commands:
			stdin, stdout, stderr = client.exec_command(command)
			streams["stdout"].append([line for line in stdout])
			streams["stderr"].append([line for line in stderr])
	return streams

def get_sbc_fw_uploads_folder():
	return "{}/sbc_interface/sbc_fw_uploads".format(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
