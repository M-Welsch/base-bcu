import os
import daemon
from queue import Queue

from time import sleep

from base.common.config import Config
from base.common.base_logging import Logger
from base.common.tcp import TCPServerThread
from base.hwctrl.hwctrl import HWCTRL
from base.webapp.webapp import Webapp
from base.schedule.scheduler import BaseScheduler
from base.backup.backup import BackupManager
from base.daemon.mounting import MountManager
from base.common.utils import *


class Daemon:
	def __init__(self, autostart_webapp=True, daemonize=True):
		self._autostart_webapp = autostart_webapp
		self._command_queue = Queue()
		self._config = Config("base/config.json")
		self._scheduler = BaseScheduler()
		self._logger = Logger(self._config.logs_directory)
		self._mount_manager = MountManager(self._config.mounting_config, self._logger)
		self._backup_manager = BackupManager(self._config.backup_config, self._logger)
		self._hardware_control = HWCTRL(self._config.hwctrl_config, self._logger)
		self._tcp_server_thread = TCPServerThread(queue=self._command_queue, logger=self._logger)
		self._webapp = Webapp(self._logger)
		if daemonize:
			self.run_as_daemon()
		else:
			self.run_not_as_daemon()


	def start_threads_and_mainloop(self):
		self._hardware_control.start()
		self._tcp_server_thread.start()
		if self._autostart_webapp:
			self._webapp.start()
		self.mainloop()

	def stop_threads(self):
		self._logger.shutdown()
		self._hardware_control.terminate()
		self._tcp_server_thread.terminate()
		self._webapp.terminate()

	def get_status(self):
		#raise NotImplementedError
		# TODO: implement hardware status retrieval
		# next_bu_time = read_next_scheduled_backup_time()
		seconds_to_next_bu = self._scheduler.seconds_to_next_bu()
		next_backup_scheduled = self._scheduler.next_backup_scheduled()
		next_backup_scheduled_string = next_backup_scheduled.strftime("%d.%m.%Y %H:%M")
		self._hardware_control.display("{}\nETA {}s".format(next_backup_scheduled_string, seconds_to_next_bu),2)

	def run_as_daemon(self):
		print("starting daemon...")
		self._logger.info("started base as daemon")
		with daemon.DaemonContext(working_directory=os.getcwd()):
			# sys.stdout = self._logging_queue fixme
			# sys.stderr = self._logging_queue fixme
			self.start_threads_and_mainloop()

	def run_not_as_daemon(self):
		self._logger.info("started BaSe without daemon (debug-mode)")
		print("starting daemon (not actually as daemon)...")
		self.start_threads_and_mainloop()

	def mainloop(self):
		terminate_flag = False
		while not terminate_flag:
			sleep(self._config.main_loop_interval)
			status_quo = self._look_up_status_quo()
			command_list = self._derive_command_list(status_quo)
			terminate_flag = self._execute_command_list(command_list)
		self.stop_threads()

	def _look_up_status_quo(self):
		status_quo = {}
		status_quo["pressed_buttons"] = self._hardware_control.pressed_buttons()
		status_quo["tcp_commands"] = []
		while not self._command_queue.empty():
			status_quo["tcp_commands"].append(self._command_queue.get())
			self._command_queue.task_done()
		status_quo["backup_scheduled_for_now"] = self._scheduler.is_backup_scheduled()
		# TODO: consider weather
		if status_quo_not_empty(status_quo): self._logger.debug("Command Queue contents: {}".format(status_quo))
		return status_quo


	def _derive_command_list(self, status_quo):
		command_list = []
		if "test_mounting" in status_quo["tcp_commands"]:
			return ["dock", "mount"] #Todo: remove "dock"??
		if "test_unmounting" in status_quo["tcp_commands"]:
			return ["unmount"]
		if "test_docking" in status_quo["tcp_commands"]:
			return ["dock"]
		if "test_undocking" in status_quo["tcp_commands"]:
			return ["undock"]
		if "reload_config" in status_quo["tcp_commands"]:
			command_list.append("reload_config")
		if status_quo["pressed_buttons"][0] or "show_status_info" in status_quo["tcp_commands"]:
			command_list.append("show_status_info")
		if status_quo["pressed_buttons"][1] or "backup" in status_quo["tcp_commands"] or status_quo["backup_scheduled_for_now"]:
			command_list.extend(["dock", "mount", "backup", "unmount", "undock"])
		if "terminate_daemon" in status_quo["tcp_commands"]:
			command_list.append("terminate_daemon")

		return command_list

	def _execute_command_list(self, command_list):
		for command in command_list:
			try:
				if command == "dock":
					self._hardware_control.dock_and_power()
				elif command == "undock":
					self._hardware_control.unpower_and_undock()
				elif command == "mount":
					self._mount_manager.mount_hdds()
				elif command == "unmount":
					self._mount_manager.unmount_hdds()
				elif command == "backup":
					self._scheduler.backup_suggested = False
					self._backup_manager.backup()
				elif command == "reload_config":
					self._config.reload()
				elif command == "show_status_info":
					self.get_status()
				elif command == "terminate_daemon":
					return True
				else:
					raise RuntimeError("'{}' is not a valid command!".format(command))
			except Exception as e:
				self._logger.error("Some command went somehow wrong: {}".format(e))
				raise e
		return False
