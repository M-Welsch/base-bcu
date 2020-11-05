import json
import os
import sys
from time import sleep, time

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

from datetime import datetime

from base.common.utils import run_external_command_as_generator, run_external_command_as_generator_shell, check_path_end_slash_and_asterik, network_available
from base.common.ssh_interface import SSHInterface
from base.common.nas_finder import NasFinder
from base.backup.rsync_wrapper import RsyncWrapperThread
from base.common.exceptions import *


class BackupManager:
	def __init__(self, backup_config, logger, mount_manager, hwctrl, set_backup_finished_flag):
		self._backup_config = backup_config
		self._logger = logger
		self._mount_manager = mount_manager
		self._hwctrl = hwctrl
		self._set_backup_finished_flag = set_backup_finished_flag
		self._set_backup_finished_flag = set_backup_finished_flag
		self._sample_interval = backup_config["sample_interval"]
		self._ssh_host = backup_config["ssh_host"]
		self._ssh_user = backup_config["ssh_user"]
		self._new_backup_folder = None
		self._nas_properties = None
		self._docking_trials = 0

	def backup(self):
		successfully_started_flag = False
		try:
			self.execute_backup()
			successfully_started_flag = True
		except NetworkError:
			self._logger.error("Network not available")
		except NasNotAvailableError:
			print("catching")
			self._logger.error("NAS not available. Backup NOT executed")
		except DockingError:
			self._logger.error("Docking Error occured. Backup NOT executed")
		except MountingError:
			self._logger.error(f"Mounting Error: {MountingError.logger_error_message}")
		except NewBuDirCreationError:
			self._logger.error("could not create directory for new backup")

		if not successfully_started_flag:
			self._set_backup_finished_flag()

	def execute_backup(self):
		self._wait_for_network_connection()
		if self._nas_available():
			self._stop_services_on_nas()
		else:
			raise NasNotAvailableError

		self._hwctrl.dock_and_power()
		self._mount_manager.mount_hdd()
		try:
			self._free_space_on_backup_hdd_if_necessary()
			newest_backup = self._get_newest_backup_dir_path()
		except BackupHddAccessError:
			if self._docking_trials < 3:
				self._logger.info("Undocking and Docking again ...")
				self._hwctrl.unpower_and_undock()
				self._docking_trials += 1
				self.run() # try again
			else:
				self._logger.error("Tried undocking and docking for 3 times. Aborting now.")

		self._create_folder_for_backup()
		self._copy_newest_backup_with_hardlinks(newest_backup)
		self._execute_backup_with_rsync()
		#self._start_services_on_nas()

	def _wait_for_network_connection(self):
		start_time = time()
		if not network_available():
			self._logger.warning("Network not available! Waiting for connection for 60 seconds ...")
			while not network_available() and not time() - start_time < 60:
				sleep(1)
			if not network_available():
				raise NetworkError
			else:
				self._logger.info(f"Network available after {time() - start_time} seconds!")

	def _nas_available(self):
		nas_finder = NasFinder(self._logger, self._backup_config)
		return nas_finder.nas_available(self._ssh_host, self._ssh_user)

	def _stop_services_on_nas(self):
		with SSHInterface(self._logger) as ssh:
			ssh.connect(self._ssh_host, self._ssh_user)
			self._enquire_nas_properties(ssh)
			self._enquire_services_to_stop_on_nas()
			if not self._list_of_services:
				self._list_of_services = ["smbd", "nginx"]
				self._logger.warning(f"Services on NAS to be stopped/restarted is not clearly stated. Stopping {self._list_of_services}")
			self._stop_list_of_services_on_nas(ssh)

	def _enquire_nas_properties(self, ssh):
		stdout, stderr = ssh.run('cat nas_for_backup')
		try:
			nas_properties = json.loads(stdout)
			self._logger.info(f"NAS variant is identified as {nas_properties['name']}")
		except json.JSONDecodeError:
			nas_properties = None
			self._logger.warning("NAS variant could not be identified!")
		self._nas_properties = nas_properties

	def _enquire_services_to_stop_on_nas(self):
		self._list_of_services = self._nas_properties["services_to_stop"]

	def _stop_list_of_services_on_nas(self, ssh):
		for service in self._list_of_services:
			if self._ssh_user == "root":
				ssh.run(f"systemctl stop {service}")
			else:
				ssh.run(f"echo {self._ssh_user} | sudo -S systemctl stop {service}")
		#Todo: test if this command stops services on a non-root login

	def _free_space_on_backup_hdd_if_necessary(self):
		while not self.enough_space_for_full_backup():
			self.delete_oldest_backup()

	def enough_space_for_full_backup(self):
		out = run_external_command_as_generator(["df", "--output=avail", "/media/BackupHDD"])
		free_space_on_bu_hdd = self.remove_heading_from_df_output(out)
		space_needed_for_full_bu = self.space_occupied_on_nas_hdd()
		print("Space free on BU HDD: {}, Space needed: {}".format(free_space_on_bu_hdd, space_needed_for_full_bu))
		self._logger.info("Space free on BU HDD: {}, Space needed: {}".format(free_space_on_bu_hdd, space_needed_for_full_bu))
		if free_space_on_bu_hdd > space_needed_for_full_bu:
			return True
		else:
			return False

	def remove_heading_from_df_output(self, df_output):
		df_output_cleaned = ""
		for line in df_output:
			if not line.strip() == "Avail":
				df_output_cleaned = int(line.strip())
		return int(df_output_cleaned)

	def space_occupied_on_nas_hdd(self):
		with SSHInterface(self._logger) as ssh:
			ssh.connect(self._ssh_host, self._ssh_user)
			space_occupied = int(ssh.run_and_raise('df --output="used" /mnt/HDD | tail -n 1'))
		return space_occupied

	def delete_oldest_backup(self):
		with BackupBrowser(self._backup_config, self._logger) as bb:
			oldest_backup = bb.get_oldest_backup()
		self._logger.info("deleting {} to free space for new backup".format(oldest_backup))

	def _get_newest_backup_dir_path(self):
		with BackupBrowser(self._backup_config, self._logger) as bb:
			return bb.get_newest_backup_abolutepath()

	def _create_folder_for_backup(self):
		path = self._get_path_for_new_bu_directory()
		print(f"create new folder: {path}")
		self._create_that_very_directory(path)
		self._check_whether_directory_was_created(path)

	def _get_path_for_new_bu_directory(self):
		timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
		path = os.path.join(self._backup_config["local_backup_target_location"], f"backup_{timestamp}")
		return path

	def _create_that_very_directory(self, path):
		try:
			os.mkdir(path)
		except OSError:
			self._logger.error(
				f'Could not create directory for new backup in {self._backup_config["local_backup_target_location"]}')

	def _check_whether_directory_was_created(self, path):
		if os.path.isdir(path):
			self._logger.info(f'Created directory for new backup: {path}')
			self._new_backup_folder = path
		else:
			self._logger.error(f"Directory {path} wasn't created!")
			raise NewBuDirCreationError

	def _copy_newest_backup_with_hardlinks(self, newest_backup):
		if newest_backup:
			# Fixme: somehow it doesnt find the source path ...
			newest_backup = check_path_end_slash_and_asterik(newest_backup)
			copy_command = f"cp -al {newest_backup} {self._new_backup_folder}"
			print(f"copy command: {copy_command}")
			for line in run_external_command_as_generator_shell(copy_command):
				print(f"copying with hl: {line}")

	def _execute_backup_with_rsync(self):
		self._sync_thread = RsyncWrapperThread(
			host=self._ssh_host,
			user=self._ssh_user,
			remote_source_path=self._backup_config["remote_backup_source_location"],
			local_target_path=self._new_backup_folder,
			set_backup_finished_flag=self._set_backup_finished_flag,
			logger=self._logger
		)
		self._sync_thread.start()

	def _start_services_on_nas(self):
		with SSHInterface(self._logger) as ssh:
			self._logger.info(f"Starting services on NAS: {self._list_of_services}")
			ssh.connect(self._ssh_host, self._ssh_user)
			self._restart_list_of_services_on_nas(ssh)

	def _restart_list_of_services_on_nas(self, ssh):
		for service in self._list_of_services:
			if self._ssh_user == "root":
				ssh.run(f"systemctl start {service}")
			else:
				ssh.run(f"echo {self._ssh_user} | sudo -S systemctl start {service}")

	def terminate(self):
		self._logger.warning("Backup Aborted")
		self._sync_thread.terminate()
		self._mark_current_backup_as_incomplete()

	def _mark_current_backup_as_incomplete(self):
		os.rename(self._new_backup_folder, f"{self._new_backup_folder}_incomplete")


class BackupBrowser:
	def __init__(self, backup_config, logger):
		self._backup_config = backup_config
		self._logger = logger

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, exc_traceback):
		pass

	def list_backups_by_age(self):
		# lowest index is the oldest
		list_of_backups = []
		try:
			for file in os.listdir(self._backup_config["local_backup_target_location"]):
				if file.startswith("backup"):
					list_of_backups.append(file)
		except OSError as e:
			self._logger.error(f"BackupHDD cannot be accessed! {e}")
			raise BackupHddAccessError
		list_of_backups.sort()
		return list_of_backups

	def get_oldest_backup(self):
		backups = self.list_backups_by_age()
		if backups:
			return backups[0]
		else:
			return ""

	def get_newest_backup_abolutepath(self):
		backups = self.list_backups_by_age()
		if backups:
			return os.path.join(self._backup_config["local_backup_target_location"], backups[-1])
		else:
			return ""


if __name__ == "__main__":
	path_to_module = "/home/base"
	sys.path.append(path_to_module)
	bm = BackupManager({"sample_interval": 0.2, "ssh_host": "192.168.0.43", "ssh_user": "pi"}, None)
	bm.backup()