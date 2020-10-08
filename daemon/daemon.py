from queue import Queue

from time import sleep
from typing import Dict, List

from base.codebooks.codebooks import *
from base.common.config import Config
from base.common.base_logging import Logger
from base.common.tcp import TCPServerThread
from base.hwctrl.hwctrl import HWCTRL
from base.webapp.webapp import Webapp
from base.schedule.scheduler import BaseScheduler
from base.backup.backup import BackupManager
from base.daemon.mounting import MountManager
from base.common.utils import *
from base.common.readout_hdd_parameters import readout_parameters_of_all_hdds
from base.sbu_interface.sbu_updater import *
from base.sbu_interface.sbu_communicator import *
from base.hwctrl.display import *


class Daemon:
	def __init__(self, autostart_webapp: bool = True):
		self._autostart_webapp = autostart_webapp
		self._command_queue = Queue()
		self._tcp_codebook = TCP_Codebook()
		self._config = Config("base/config.json")
		self._scheduler = BaseScheduler()
		self._logger = Logger(self._config.logs_directory)
		self._mount_manager = MountManager(self._config.mounting_config, self._logger)
		self._backup_manager = BackupManager(self._config.backup_config, self._logger)
		self._hardware_control = HWCTRL(self._config.hwctrl_config, self._logger)
		self._tcp_server_thread = TCPServerThread(queue=self._command_queue, logger=self._logger)
		self._webapp = Webapp(self._logger)
		self._start_sbu_communicator_on_hw_rev3_and_set_sbu_rtc()
		self._display = Display(self._hardware_control, self._sbu_communicator, self._config)
		self._shutdown_flag = False
		self._display_menu_pointer = 'Main'
		self.start_threads_and_mainloop()

	def _start_sbu_communicator_on_hw_rev3_and_set_sbu_rtc(self):
		if self._hardware_control.get_hw_revision() == 'rev3':
			self._sbu_communicator = SbuCommunicator(self._hardware_control, self._logger, self._config.sbu_communicator_config)


	def start_threads_and_mainloop(self):
		self._hardware_control.start()
		self._tcp_server_thread.start()
		if self._autostart_webapp:
			self._webapp.start()
		self.mainloop()

	def stop_threads(self):
		self._display.write("Goodbye", "BCU stopping")
		self._sbu_communicator.terminate() # needs active hwctrl to shutdown cleanly!
		self._hardware_control.terminate()
		self._tcp_server_thread.terminate()
		self._webapp.terminate()
		self._logger.terminate()

	def mainloop(self):
		self._sbu_communicator.set_display_brightness_percent(100)
		self._hmi_show_main_menu()
		self._terminate_flag = False
		while not self._terminate_flag:
			sleep(self._config.main_loop_interval)
			status_quo = self._look_up_status_quo()
			command_list = self._derive_command_list(status_quo)
			self._execute_command_list(command_list)
			
		if self._shutdown_flag:
			self._initiate_shutdown_process()
		else:
			self.stop_threads()

	def _hmi_show_main_menu(self):
		self._display.write("BaSe   show IP > ", "          Demo >")

	def _seconds_to_next_bu_to_sbu(self):
		seconds_to_next_bu = self._scheduler.seconds_to_next_bu()
		self._sbu_communicator.send_seconds_to_next_bu_to_sbu(seconds_to_next_bu)

	def _look_up_status_quo(self) -> Dict:
		status_quo = {
			"pressed_buttons": self._hardware_control.pressed_buttons(),
			"tcp_commands": []
		}
		while not self._command_queue.empty():
			status_quo["tcp_commands"].append(self._command_queue.get())
			self._command_queue.task_done()
		status_quo["backup_scheduled_for_now"] = self._scheduler.is_backup_scheduled()
		# TODO: consider weather
		if status_quo_not_empty(status_quo):
			self._logger.debug(f"Command Queue contents: {status_quo}")
		return status_quo

	@staticmethod
	def _derive_command_list(status_quo: Dict) -> List[str]:
		command_list = []
		if "test_mounting" in status_quo["tcp_commands"]:
			return ["mount"]
		if "test_unmounting" in status_quo["tcp_commands"]:
			return ["unmount"]
		if "test_docking" in status_quo["tcp_commands"]:
			return ["dock"]
		if "test_undocking" in status_quo["tcp_commands"]:
			return ["undock"]
		if "reload_config" in status_quo["tcp_commands"]:
			command_list.append("reload_config")
		if "update_sbc" in status_quo["tcp_commands"]:
			return ["update_sbc"]
		if "readout_hdd_parameters" in status_quo["tcp_commands"]:
			return ["readout_hdd_parameters"]
		if "new_buhdd" in status_quo["tcp_commands"]:
			return ["enter_new_buhdd_in_config.json"]
		if "show_status_info" in status_quo["tcp_commands"]:
			command_list.append("show_status_info")
		# if (
		# 		status_quo["pressed_buttons"][1] or
		# 		"backup" in status_quo["tcp_commands"] or
		# 		status_quo["backup_scheduled_for_now"
		# ):
		#  command_list.extend(["dock", "mount", "backup", "unmount", "undock"])

		if status_quo["pressed_buttons"][0]: # show IP Adress on Display
			command_list.append("show_ip_on_display")
		if status_quo["pressed_buttons"][1]: # demo
			command_list.extend(["dock", "wait", "undock"])
		if "terminate_daemon" in status_quo["tcp_commands"]:
			command_list.append("terminate_daemon")
		if "terminate_daemon_and_shutdown" in status_quo["tcp_commands"]:
			command_list.append("terminate_daemon_and_shutdown")
		if "seconds_to_next_bu_to_sbc" in status_quo["tcp_commands"]:
			self._seconds_to_next_bu_to_sbu()
		if "shutdown_base" in status_quo["tcp_commands"]:
			self._communicate_shutdown_intention_to_sbu()
		if command_list:
			print("command list:", command_list)
		return command_list

	@staticmethod
	def _extract_sbc_filename_from_commmand(status_quo_tcp_commands: List) -> str:
		sbc_filename = None
		for entry in status_quo_tcp_commands:
			if entry[:10] == "update_sbc":
				sbc_filename = entry[:14]
		return sbc_filename

	def _execute_command_list(self, command_list: List[str]):
		for command in command_list:
			try:
				if command == "dock":
					self._hardware_control.dock_and_power()
				elif command == "wait":
					self._wait_for_seconds(10)
				elif command == "undock":
					self._hardware_control.unpower_and_undock()
				elif command == "mount":
					print("_execute_command_list: mount")
					self._mount_manager.mount_hdd()
				elif command == "unmount":
					self._mount_manager.unmount_hdd()
				elif command == "backup":
					self._scheduler.backup_suggested = False
					self._backup_manager.backup()
				elif command == "reload_config":
					self._config.reload()
				elif command == "show_status_info":
					self.get_status()
				elif command == "show_ip_on_display":
					self.show_ip_address_on_display()
				elif command == "terminate_daemon":
					self._terminate_flag = True
					return True
				elif command == "terminate_daemon_and_shutdown":
					self._initiate_shutdown_process()
					self._shutdown_flag = True
					return True
				elif command == "update_sbc":
					self.update_sbc()
				elif command == "readout_hdd_parameters":
					self.read_and_send_hdd_parameters()
				elif command == "enter_new_buhdd_in_config.json":
					self.update_bu_hdd_in_config_file()
				else:
					raise RuntimeError(f"'{command}' is not a valid command!")
			except Exception as e:
				self._logger.error(f"Some command went somehow wrong: {e}")
				raise e
		return False

	def _wait_for_seconds(self, pause_duration):
		sleep(pause_duration)

	def get_status(self):
		# TODO: implement hardware status retrieval
		# next_bu_time = read_next_scheduled_backup_time()
		seconds_to_next_bu = self._scheduler.seconds_to_next_bu()
		next_backup_scheduled = self._scheduler.next_backup_scheduled()
		next_backup_scheduled_string = next_backup_scheduled.strftime("%d.%m.%Y %H:%M")
		# self._hardware_control.display("{}\nETA {}s".format(next_backup_scheduled_string, seconds_to_next_bu), 2)
		# uncomment line above once SBC-Display forwarding works!

		# TODO: send to Webapp if it asks for status ...
		backups_present = list_backups_by_age(self._config.mounting_config["backup_hdd_mount_point"])

	def show_ip_address_on_display(self):
		if self._display_menu_pointer == 'IP':
			self._hmi_show_main_menu()
			self._display_menu_pointer = 'Main'
		else:
			IP = get_ip_address()
			self._display.write('Local IP: back >', IP)
			self._display_menu_pointer = 'IP'

	def update_sbc(self):
		# Fixme: that crashes the ttyS1 for some reason
		print("updating SBU")
		self._display.write("Updating SBU","Firmware")
		self._sbu_communicator.terminate()
		self._sbu_updater = SbuUpdater(self._hardware_control)
		self._sbu_updater.update_sbu()
		self._start_sbu_communicator_on_hw_rev3_and_set_sbu_rtc()
		self._hmi_show_main_menu()
		# SBC_U = SBC_Updater()
		# SBC_U.update_sbc()

	def read_and_send_hdd_parameters(self):
		try:
			# request the result one second before TCP Server's timeout elapses
			timeout = self._tcp_codebook.commands["readout_hdd_parameters"].Timeout - 1
			wait_for_new_device_file(timeout)
		except RuntimeError as e:
			print(e)
		answer = readout_parameters_of_all_hdds()
		self._tcp_server_thread.write_answer(answer)

	def update_bu_hdd_in_config_file(self):
		self._config.write_BUHDD_parameter_to_tmp_config_file()

	def _initiate_shutdown_process(self):
		self._logger.info("Shutting down")
		self._sbu_communicator.send_shutdown_request()
		self._seconds_to_next_bu_to_sbu()
		self.stop_threads()
		self._shutdown_base()

	def _shutdown_base(self):
		os.system("shutdown -h now")