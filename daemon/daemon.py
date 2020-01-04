import os
import daemon
from queue import Queue

from time import sleep

from base.common.base_queues import LoggingQueue
from base.common.config import Config
from base.schedule.scheduler import Scheduler
from base.common.base_logging import Logger
from base.hwctrl.hwctrl import HWCTRL
from base.common.tcp import TCPServerThread
from base.webapp.index import Webapp
from base.backup.backup import BackupManager

class MountManager:
	@staticmethod
	def _mount():
		pass  # TODO: implement

	@staticmethod
	def _unmount():
		pass  # TODO: implement


def get_status():
	pass  # TODO: implement


class Daemon:
	def __init__(self, autostart_webapp=True, daemonize=True):
		self._autostart_webapp = autostart_webapp
		self._logging_queue = LoggingQueue()
		self._log = self._logging_queue.push_msg
		self._command_queue = Queue()
		self._config = Config("base/config.json")
		self._scheduler = Scheduler()
		self._logger = Logger(self._logging_queue, self._logging_queue.work_off_msg)
		self._hardware_control = HWCTRL(self._logging_queue.push_msg)
		self._tcp_server_thread = TCPServerThread(queue=self._command_queue, push_msg=self._logging_queue.push_msg)
		self._webapp = Webapp()
		if daemonize:
			self.run_as_daemon()
		else:
			self.run_not_as_daemon()


	def start_threads_and_mainloop(self):
		self._logger.start()
		self._hardware_control.start()
		self._tcp_server_thread.start()
		if self._autostart_webapp:
			self._webapp.start()
		self.mainloop()

	def run_as_daemon(self):
		print("starting daemon...")
		self._log("started base as daemon")
		with daemon.DaemonContext(working_directory=os.getcwd()):
			# sys.stdout = self._logging_queue fixme
			# sys.stderr = self._logging_queue fixme
			self.start_threads_and_mainloop()

	def run_not_as_daemon(self):
		self._log("started BaSe without daemon (debug-mode)")
		print("starting daemon (not actually as daemon)...")
		self.start_threads_and_mainloop()

	def mainloop(self):
		while True:
			sleep(1)  # TODO: Use from logfile
			status_quo = self._look_up_status_quo()
			command_list = self._derive_command_list(status_quo)
			self._execute_command_list(command_list)

	def _look_up_status_quo(self):
		status_quo = {}
		status_quo["pressed_buttons"] = self._hardware_control.pressed_buttons()
		status_quo["tcp_commands"] = []
		while not self._command_queue.empty():
			status_quo["tcp_commands"].append(self._command_queue.get())
			self._command_queue.task_done()
		self._log("Command Queue contents: {}".format(status_quo["tcp_commands"]), "debug")
		status_quo["backup_scheduled_for_now"] = False  # TODO: consider schedule
		# consider weather
		return status_quo

	def _derive_command_list(self, status_quo):
		command_list = []
		if "reload_config" in status_quo["tcp_commands"]:
			command_list.append("reload_config")
		if status_quo["pressed_buttons"][0] or "show_status_info" in status_quo["tcp_commands"]:
			command_list.append("show_status_info")
		if status_quo["pressed_buttons"][1] or "backup" in status_quo["tcp_commands"] or status_quo["backup_scheduled_for_now"]:
			command_list.extend(["dock", "mount", "backup", "unmount", "undock"])
		return command_list

	def _execute_command_list(self, command_list):
		for command in command_list:
			try:
				if command == "dock":
					self._hardware_control.dock_and_power()
				elif command == "undock":
					self._hardware_control.unpower_and_undock()
				elif command == "mount":
					MountManager._mount()
				elif command == "unmount":
					MountManager._unmount()
				elif command == "backup":
					BackupManager.backup()
				elif command == "reload_config":
					self._config.reload()
				elif command == "show_status_info":
					get_status()
				else:
					raise RuntimeError("'{}' is not a valid command!".format(command))
			except Exception as e:
				self._log("Some command went somehow wrong: {}".format(e), "error")
