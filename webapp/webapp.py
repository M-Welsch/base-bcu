from platform import system
if system() == "Linux":
	from sysdmanager import SystemdManager
else:
	from base.mockups.mockupsysdmanager import SystemdManager

class Webapp:
	def __init__(self, logger):
		self._manager = SystemdManager()
		self.logger = logger

	def start(self):
		if not self._manager.is_active("base-webapp.service"):
			self.logger.info("base-webapp not running yet, starting now")
			self._manager.start_unit("base-webapp.service")
		else:
			print("base-webapp already running")

	def terminate(self):
		if self._manager.is_active("base-webapp.service"):
			self.logger.info("base-webapp running. Stopping ..")
			self._manager.stop_unit("base-webapp.service")
		else:
			print("base-webapp not running")
