import os
from time import time
from subprocess import run, Popen, PIPE, STDOUT


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