from os import path

from base.common.utils import wait_for_device_file, run_external_command, list_backups_by_age


class MountManager:
	def __init__(self, config, logger):
		self._logger = logger
		self.b_hdd_device = config["backup_hdd_device_file_path"]
		self.b_hdd_fsys = config["backup_hdd_file_system"]
		self.b_hdd_mount = config["backup_hdd_mount_point"]
		self.b_timeout = config["backup_device_file_timeout"]

	def mount_hdd(self):
		print("mount_hdd:", self._backup_hdd_mounted(), self._backup_hdd_available())
		if not self._backup_hdd_mounted() and self._backup_hdd_available():
			self._mount_backup_hdd()

	def unmount_hdd(self):
		if self._backup_hdd_mounted():
			self._unmount_backup_hdd()

	def _backup_hdd_mounted(self):
		return path.ismount(self.b_hdd_mount)

	def _backup_hdd_available(self):
		try:
			wait_for_device_file(self.b_hdd_device, self.b_timeout)
			# TODO: Ensure that the right HDD is found. (identifier-file?)
			return True
		except RuntimeError as e:
			self._logger.error(e)
			return False

	def _mount_backup_hdd(self):
		print("_mount_backup_hdd: Trying to mount backup HDD...")
		command = ["mount", "-t", self.b_hdd_fsys,
				   self.b_hdd_device, self.b_hdd_mount]
		success_msg = "Mounting backup HDD probably successful."
		error_msg = "Failed mounting backup HDD. Traceback:"
		run_external_command(command, success_msg, error_msg)

	def _unmount_backup_hdd(self):
		print("Trying to unmount backup HDD...")
		command = ["sudo", "umount", self.b_hdd_mount]
		success_msg = "Unmounting backup HDD probably successful."
		error_msg = "Failed unmounting backup HDD. Traceback:"
		run_external_command(command, success_msg, error_msg)
