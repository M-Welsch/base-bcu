import socket
import re
from time import sleep
import logging

from base.common.ssh_interface import SSHInterface
from base.common.debug_utils import dump_ifconfig


class NasFinder:
	def __init__(self, config_backup):
		self._config_backup = config_backup

	def nas_available(self, target_ip, target_user):
		return self._nas_ip_available(target_ip) and self._nas_correct(target_ip, target_user)

	def _nas_ip_available(self, target_ip):
		connection_trials = 0
		max_connection_trials = self._config_backup["nas_finder_maximum_connection_trials"]
		response = False
		while connection_trials < max_connection_trials and not response:
			t_ip = socket.gethostbyname(target_ip)
			ssh_port = 22
			s = socket. \
				socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				s.connect((t_ip, ssh_port))
				print(f"NAS Finder: {target_ip}:{ssh_port} open!")
				response = True
			except OSError as e:
				if "Errno 101" in str(e):
					# network unreachable
					logging.warning(f'Nas Finder. Network is unreachable! OSError: {e}')
					dump_ifconfig()
					connection_trials += 1
				elif "Errno 113" in str(e):
					# No route to host
					logging.warning(f'NAS Finder: {target_ip}:{ssh_port} is not open! OSError: {e}')
					connection_trials += 1
				sleep(self._config_backup["nas_finder_wait_seconds_between_connection_trials"])
			finally:
				s.close()

		if not response:
			logging.error(
				f'NAS Finder: {target_ip}:{ssh_port} is not open! Tried {max_connection_trials} times with '
				f'{self._config_backup["nas_finder_wait_seconds_between_connection_trials"]} pause'
			)
			print(f"NAS Finder: {target_ip}:{ssh_port} is not open!")
		return response

	def _nas_correct(self, target_ip, target_user):
		response = None
		with SSHInterface() as SSHI:
			if SSHI.connect(target_ip, target_user) == 'Established':
				response = self.check_connected_nas(SSHI, target_ip)
		return response

	def _nas_hdd_mounted(self, target_ip, target_user):
		response = None
		with SSHInterface() as SSHI:
			if SSHI.connect(target_ip, target_user) == 'Established':
				response = self._check_nas_hdd_mounted(SSHI)
		return response

	@staticmethod
	def check_connected_nas(sshi, target_ip):
		stdout, stderr = sshi.run('cat nas_for_backup')
		if stderr:
			logging.error(
				f"NAS on {target_ip} is not the correct one? Couldn't open file 'nas_for_backup'. Error = {stderr}")
			response = False
		if 'DietPi' in stdout:  # Fixme: cleaner! Its a json file now
			logging.info(f"found correct NAS on {target_ip}")
			response = True
		return response

	def _check_nas_hdd_mounted(self, sshi):
		nas_hdd_path = self._config_backup["remote_backup_source_location"]
		sshi.run(f'cd {nas_hdd_path}')
		sleep(1)
		stdout, stderr = sshi.run(f'mount | grep HDD')
		print(f"command = 'mount | grep HDD' on nas, stdout = {stdout}, stderr = {stderr}")
		logging.info(f"command = 'mount | grep HDD' on nas, stdout = {stdout}, stderr = {stderr}")
		if re.search("sd.. on /mnt/HDD type ext4", stdout):
			return True
		else:
			return False
