import json


class Config:
	__instance = None

	@staticmethod
	def global_instance():
		""" static access method. """
		if Config.__instance is None:
			Config()
		return Config.__instance

	def __init__(self):
		if Config.__instance is not None:
			raise Exception("This class is a singleton!")
		Config.__instance = self
		self._path = "base/config.json"
		self._load()

	def _load(self):
		with open(self._path, 'r') as cf:
			self._config = json.load(cf)

	@property
	def logs_directory(self):
		return self._config["Logging"]["logs_directory"]

	@property
	def main_loop_interval(self):
		return self._config["Daemon"]["main_loop_interval"]

	@property
	def tcp_port(self):
		return self._config["Daemon"]["dm_listens_to_port"]

	@property
	def config_schedule(self):
		return self._config["Schedule"]

	@property
	def config_hwctrl(self):
		return self._config["HWCTRL"]

	@property
	def config_sbu_communicator(self):
		return self._config["SBU_Communicator"]

	@property
	def config_hmi(self):
		return self._config["HMI"]

	@property
	def config_mounting(self):
		return self._config["Mounting"]

	@property
	def config_backup(self):
		return self._config["Backup"]

	@property
	def config_daemon(self):
		return self._config["Daemon"]

	@property
	def config_shutdown(self):
		return self._config["Shutdown"]

	def update(self):
		with open(self._path, 'w') as cf:
			json.dump(self._config, cf)
	
	def reload(self):
		self._load()

	def write_BUHDD_parameter_to_tmp_config_file(self):
		f = open("/tmp/hdd_parameters_of_buhdd_to_use", "r")
		hdd_params_str = f.read()
		f.close()
		hdd_parameters = json.loads(hdd_params_str)
		self._config['Device Specific']['Backup HDD Device Signature']['Model Number'] = hdd_parameters["Model Number"]
		self._config['Device Specific']['Backup HDD Device Signature']['Serial Number'] = hdd_parameters["Serial Number"]
		self.update()