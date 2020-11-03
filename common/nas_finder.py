import socket
from time import sleep
from base.common.ssh_interface import SSHInterface


class NasFinder:
	def __init__(self, logger, config_backup):
		self._logger = logger
		self._config_backup = config_backup

	def nas_available(self, target_ip, target_user):
		return self._nas_ip_available(target_ip) and self._nas_correct(target_ip, target_user)

	def _nas_ip_available(self, target_ip):
		connection_trials = 0
		max_connection_trials = self._config_backup["nas_finder_maximum_connection_trials"]
		response = False
		while connection_trials < max_connection_trials and not response:
			t_IP = socket.gethostbyname(target_ip)
			ssh_port = 22
			s = socket. \
				socket(socket.AF_INET, socket.SOCK_STREAM)

			conn = s.connect_ex((t_IP, ssh_port))
			if conn == 0:
				self._logger.info(f"NAS Finder: {target_ip}:{ssh_port} open!")
				print(f"NAS Finder: {target_ip}:{ssh_port} open!")
				response = True
			elif conn == 101:
				self._logger.warning(f'Nas Finder. Network is unreachable!')
				connection_trials += 1
			else:
				self._logger.warning(f'NAS Finder: {target_ip}:{ssh_port} is not open! "Conn" = {conn}')
				connection_trials += 1
				sleep(self._config_backup["nas_finder_wait_seconds_between_connection_trials"])
			s.close()
		if not response:
			self._logger.error(f'NAS Finder: {target_ip}:{ssh_port} is not open! Tried {max_connection_trials} times with {self._config_backup["nas_finder_wait_seconds_between_connection_trials"]} pause. Conn = {conn}')
			print(f"NAS Finder: {target_ip}:{ssh_port} is not open! Conn = {conn}")
		return response

	def _nas_correct(self, target_ip, target_user):
		response = None
		with SSHInterface(self._logger) as SSHI:
			if SSHI.connect(target_ip,target_user) == 'Established':
				response = self.check_connected_nas(SSHI, target_ip)
		return response

	def check_connected_nas(self, SSHI, target_ip):
		stdout, stderr = SSHI.run('cat nas_for_backup')
		if stderr:
			self._logger.error(
				f"NAS on {target_ip} is not the correct one? Couldn't open file 'nas_for_backup'. Error = {stderr}")
			response = False
		if 'DietPi' in stdout: #Fixme: cleaner! Its a json file now
			self._logger.info(f"found correct NAS on {target_ip}")
			response = True
		return response



