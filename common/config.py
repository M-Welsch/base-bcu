import json

class Config:
	def __init__(self, path):
		self._path = path
		with open(self._path, 'r') as cf:
			self._config = json.load(cf)

	@property
	def tcp_port(self):
		return int(self._config["Daemon"]["dm_listens_to_port"])

	@property
	def mounting_config(self):
		return {
			"backup_hdd_mount_point": self._config["Mounting"]["backup_hdd_mount_point"],
			"server_hdd_mount_point": self._config["Mounting"]["server_hdd_mount_point"],
			"backup_hdd_device_file_path": self._config["Mounting"]["backup_hdd_device_file_path"],
			"server_hdd_remote_path": self._config["Mounting"]["server_hdd_remote_path"],
			"backup_hdd_file_system": self._config["Mounting"]["backup_hdd_file_system"],
			"server_hdd_credentials_path": self._config["Mounting"]["server_hdd_credentials_path"]
		}
	

	def reload(self):
		pass  # TODO: implement