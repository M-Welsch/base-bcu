from base.common.utils import wait_for_new_device_file, run_external_command
from os import path


class MountManager:
	def __init__(self, config, logger):
		self._logger = logger
		self.b_hdd_device = config["backup_hdd_device_file_path"]
		self.b_hdd_fsys = config["backup_hdd_file_system"]
		self.b_hdd_mount = config["backup_hdd_mount_point"]
		self.s_hdd_remote = config["server_hdd_remote_path"]
		self.s_hdd_cred = config["server_hdd_credentials_path"]
		self.s_hdd_mount = config["server_hdd_mount_point"]
		self.b_timeout = config["backup_device_file_timeout"]

	def mount_hdds(self):
		try:
			new_device_files = wait_for_new_device_file(self.b_timeout)
			# TODO: Ensure that the right HDD is found. (identifier-file?)
		except RuntimeError as e:
			self._logger.error(e)
		self._mount_backup_hdd()
		self._mount_server_hdd()

	def unmount_hdds(self):
		if self._server_hdd_mounted():
			self._unmount_backup_hdd()
		if self._backup_hdd_mounted():
			self._unmount_server_hdd()

	def _server_hdd_mounted(self):
		return path.ismount(self.s_hdd_mount)

	def _backup_hdd_mounted(self):
		return path.ismount(self.b_hdd_mount)


	def _mount_backup_hdd(self):
		print("Trying to mount backup HDD...")
		command = ["mount", "-t", self.b_hdd_fsys,
				   self.b_hdd_device, self.b_hdd_mount]
		success_msg = "Mounting backup HDD probably successful."
		error_msg = "Failed mounting backup HDD. Traceback:"
		run_external_command(command, success_msg, error_msg)

	def _mount_server_hdd(self):
		print("Trying to mount server HDD...")
		command = ["mount", "-t", "cifs", self.s_hdd_remote, self.s_hdd_mount,
				   "-o", "credentials="+self.s_hdd_cred]
		success_msg = "Mounting server HDD probably successful."
		error_msg = "Failed mounting server HDD. Traceback:"
		run_external_command(command, success_msg, error_msg)

	def _unmount_backup_hdd(self):
		print("Trying to unmount backup HDD...")
		command = ["sudo", "umount", self.b_hdd_mount]
		success_msg = "Unmounting backup HDD probably successful."
		error_msg = "Failed unmounting backup HDD. Traceback:"
		run_external_command(command, success_msg, error_msg)

	def _unmount_server_hdd(self):
		print("Trying to unmount server HDD...")
		command = ["sudo", "umount", self.s_hdd_mount]
		success_msg = "Unmounting server HDD probably successful."
		error_msg = "Failed unmounting server HDD. Traceback:"
		run_external_command(command, success_msg, error_msg)
