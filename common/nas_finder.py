import socket
from base.common.ssh_interface import SSHInterface


class NasFinder:
	def __init__(self, logger):
		self._logger = logger

	def nas_available(self, target_ip, target_user):
		return self._nas_ip_available(target_ip) and self._nas_correct(target_ip, target_user)

	def _nas_ip_available(self, target_ip):
		t_IP = socket.gethostbyname(target_ip)
		ssh_port = 22
		s = socket.\
			socket(socket.AF_INET, socket.SOCK_STREAM)

		conn = s.connect_ex((t_IP, ssh_port))
		if conn == 0:
			self._logger.info(f"NAS Finder: {target_ip}:{ssh_port} open!")
			print(f"NAS Finder: {target_ip}:{ssh_port} open!")
			response = True
		else:
			self._logger.warning(f"NAS Finder: {target_ip}:{ssh_port} is not open!")
			print(f"NAS Finder: {target_ip}:{ssh_port} is not open!")
			response = False
		s.close()
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


