import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)

from time import sleep, time
from threading import Thread

from base.common.utils import run_external_command_as_generator_2, SSHInterface


class BackupManager:
	def __init__(self, backup_config, logger):
		self._backup_config = backup_config
		self._logger = logger
		self._backup_thread = None

	def backup(self):
		self._backup_thread = BackupThread(self._backup_config)
		self._backup_thread.start()


class BackupThread(Thread):
	def __init__(self, backup_config):
		super(BackupThread, self).__init__()
		self._sample_interval = backup_config["sample_interval"]
		self._ssh_host = backup_config["ssh_host"]
		self._ssh_user = backup_config["ssh_user"]

	def run(self):
		start = time()
		
		# TODO: check if nas is available at some point ...

		self._stop_services_on_nas()
		self._free_space_on_backup_hdd_if_necessary()
		self._create_folder_for_backup()
		self._execute_backup_with_rsync()
		self._restart_services_on_nas()

	def _stop_services_on_nas(self):
		with SSHInterface(self._ssh_host, self._ssh_user) as ssh:
			ssh.run("echo raspberry | sudo -S systemctl stop smbd")
			ssh.run("echo raspberry | sudo -S systemctl stop nginx")

	def _free_space_on_backup_hdd_if_necessary(self):
		while not self.enough_space_for_full_backup():
			self.delete_oldest_backup()

	def enough_space_for_full_backup(self):
		out = run_external_command_as_generator_2(["df", "--output=avail", "/media/BackupHDD"])
		free_space_on_bu_hdd = self.remove_heading_from_df_output(out)
		space_needed_for_full_bu = self.space_occupied_on_nas_hdd()
		print("Space free on BU HDD: {}, Space needed: {}".format(free_space_on_bu_hdd, space_needed_for_full_bu))
		#self._logger.info("Space free on BU HDD: {}, Space needed: {}".format(free_space_on_bu_hdd, space_needed_for_full_bu))
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
		with SSHInterface(self._ssh_host, self._ssh_user) as ssh:
			space_occupied = int(ssh.run_and_raise('df --output="used" /media/HDD | tail -n 1'))
		return space_occupied


	def delete_oldest_backup(self):
		oldest_backup = get_oldest_backup()
		print("deleting {} to free space for new backup".format(oldest_backup))
		# leave message in logfile
		pass

	def _create_folder_for_backup(self):
		pass

	def _execute_backup_with_rsync(self):
		"rsync -avHe ssh pi@192.168.0.43:/home/pi . --progress"

		# # for line in run_external_command_as_generator_2(["find", "/"]):
		# for line in run_external_command_as_generator_2(["grep", "-r", "-i", "e", "/home"]):
		# 	now = time()
		# 	if now - start >= self._sample_interval:
		# 		print(line.strip())
		# 		# show on display
		# 		start = now

	def _restart_services_on_nas(self):
		with SSHInterface(self._ssh_host, self._ssh_user) as ssh:
			ssh.run("echo raspberry | sudo -S systemctl start smbd")
			ssh.run("echo raspberry | sudo -S systemctl start nginx")

	def terminate(self):
		# kill rsync
		raise NotImplementedError


if __name__ == "__main__":
	path_to_module = "/home/maxi"
	sys.path.append(path_to_module)
	bm = BackupManager({"sample_interval": 0.2, "ssh_host": "192.168.0.43", "ssh_user": "pi"}, None)
	bm.backup()