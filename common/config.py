import json

class Config:
	def __init__(self, path):
		self._path = path
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
	def mounting_config(self):
		return self._config["Mounting"]
	

	def reload(self):
		pass  # TODO: implement