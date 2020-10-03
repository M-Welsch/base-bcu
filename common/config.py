import json

class Config:
	def __init__(self, path):
		self._path = path
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
	def hwctrl_config(self):
		return self._config["HWCTRL"]

	@property
	def sbu_communicator_config(self):
		return self._config["SBU_Communicator"]

	@property
	def mounting_config(self):
		return self._config["Mounting"]

	@property
	def backup_config(self):
		return self._config["Backup"]

	def _update(self):
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
		self._update()