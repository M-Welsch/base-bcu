import socket
import re
from time import sleep
import logging
from pathlib import Path

from base.common.ssh_interface import SSHInterface
from base.common.debug_utils import dump_ifconfig
from base.common.config import Config


LOG = logging.getLogger(Path(__file__).name)


# TODO: Please refactor NasFinder!


class NasFinder:
	def __init__(self):
		self._config: Config = Config("sync.json")

	def nas_available(self):
		target_ip = self._config.ssh_host
		target_user = self._config.ssh_user
		return self._nas_ip_available(target_ip) and self._nas_correct(target_ip, target_user)

	@staticmethod
	def _nas_ip_available(target):
		response = False
		ssh_port = 22
		target_ip = socket.gethostbyname(target)
		socket.setdefaulttimeout(1)  # TODO: Make argument to socket.setdefaulttimeout() configurable
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect((target_ip, ssh_port))
			LOG.info(f"NAS Finder: {target}:{ssh_port} open!")
			response = True
		except OSError as e:
			if "Errno 101" in str(e):  # network unreachable
				LOG.warning(f'Nas Finder. Network is unreachable! OSError: {e}')
				dump_ifconfig()
			elif "Errno 113" in str(e):  # No route to host
				LOG.warning(f'NAS Finder: {target}:{ssh_port} is not open! OSError: {e}')
		finally:
			sock.close()

		return response

	def _nas_correct(self, target_ip, target_user):
		response = None
		with SSHInterface() as sshi:
			if sshi.connect(target_ip, target_user) == 'Established':
				response = self.check_connected_nas(sshi, target_ip)
		return response

	def nas_hdd_mounted(self):
		response = None
		target_ip = self._config.ssh_host
		target_user = self._config.ssh_user
		with SSHInterface() as sshi:
			if sshi.connect(target_ip, target_user) == 'Established':
				response = self._check_nas_hdd_mounted(sshi)
		return response

	@staticmethod
	def check_connected_nas(sshi, target_ip):
		response = False
		stdout, stderr = sshi.run('cat nas_for_backup')
		if stderr:
			LOG.error(
				f"NAS on {target_ip} is not the correct one? Couldn't open file 'nas_for_backup'. Error = {stderr}"
			)
		if 'DietPi' in stdout:  # Fixme: cleaner! Its a json file now
			LOG.info(f"found correct NAS on {target_ip}")
			response = True
		return response

	def _check_nas_hdd_mounted(self, sshi):
		source = self._config.remote_backup_source_location
		sshi.run(f'cd {source}')
		sleep(1)
		stdout, stderr = sshi.run(f'mount | grep {source}')
		LOG.info(f"command = 'mount | grep {source}' on nas, stdout = {stdout}, stderr = {stderr}")
		return bool(re.search(f"sd.. on {source} type ext4", stdout))
