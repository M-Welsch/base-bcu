import logging
from pathlib import Path
from platform import system


log = logging.getLogger(Path(__file__).name)


if system() == "Linux":
	from sysdmanager import SystemdManager
else:
	from base.mockups.mockupsysdmanager import SystemdManager


class Webapp:
	def __init__(self):
		self._manager = SystemdManager()

	def start(self):
		if not self._manager.is_active("base-webapp.service"):
			log.info("base-webapp not running yet, starting now")
			self._manager.start_unit("base-webapp.service")
		else:
			print("base-webapp already running")

	def terminate(self):
		if self._manager.is_active("base-webapp.service"):
			log.info("base-webapp running. Stopping ..")
			self._manager.stop_unit("base-webapp.service")
		else:
			print("base-webapp not running")
