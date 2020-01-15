import os
import daemon
from queue import Queue

from time import sleep

from base.common.config import Config
from base.common.base_logging import Logger
from base.common.tcp import TCPServerThread
from base.hwctrl.hwctrl import HWCTRL
from base.webapp.webapp import Webapp
from base.schedule.scheduler import Scheduler
from base.backup.backup import BackupManager
from base.daemon.mounting import MountManager


def get_status():
	pass
	# TODO: implement:
	# next_bu_time = read_next_scheduled_backup_time()
	next_bu_time = "leet!"
	self._hardware_control.display(next_bu_time)


class Daemon:
	def __init__(self, autostart_webapp=True, daemonize=True):
		self._autostart_webapp = autostart_webapp
		self._command_queue = Queue()
		self._config = Config("base/config.json")
		self._scheduler = Scheduler()
		self._logger = Logger(self._config.logs_directory)
		self._mount_manager = MountManager(self._config.mounting_config, self._logger)
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
		self._logger.debug("Command Queue contents: {}".format(status_quo["tcp_commands"]))
		status_quo["backup_scheduled_for_now"] = False  # TODO: consider schedule
		# consider weather
		return status_quo

	def _derive_command_list(self, status_quo):
		command_list = []
		if "test_mounting" in status_quo["tcp_commands"]:
			return ["dock", "mount"]
		if "test_unmounting" in status_quo["tcp_commands"]:
			return ["unmount"]
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
					BackupManager.backup()
				elif command == "reload_config":
					self._config.reload()
				elif command == "show_status_info":
					get_status()
				elif command == "terminate_daemon":
					return True
				else:
					raise RuntimeError("'{}' is not a valid command!".format(command))
			except Exception as e:
				self._logger.error("Some command went somehow wrong: {}".format(e))
		return False
