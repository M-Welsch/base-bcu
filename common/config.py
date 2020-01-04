import json

class Config:
	def __init__(self, path):
		self._path = path
		with open(self._path, 'r') as cf:
			self._config = json.load(cf)

	@property
	def tcp_port():
		return int(self._config["Daemon"]["dm_listens_to_port"])

	def reload(self):
		pass  # TODO: implement