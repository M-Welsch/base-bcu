import os
from time import time


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