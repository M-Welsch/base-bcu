import json
import os
from typing import Any, Set


class ConfigValidationError(Exception):
	pass


class Config(dict):
	_base_dir = "python.base/base/config/"

	def __init__(self, config_file_name: str, read_only: bool = True, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._read_only: bool = read_only
		self._config_path: str = os.path.join(self._base_dir, config_file_name)
		self._initialized: bool = True
		self.reload()

	@classmethod
	def set_config_base_dir(cls, base_dir):
		cls._base_dir = base_dir

	def reload(self) -> None:
		with open(self._config_path, "r") as jf:
			self.update(json.load(jf))

	def save(self) -> None:
		with open(self._config_path, "w") as jf:
			json.dump(self, jf)

	def assert_keys(self, keys: Set[str]):
		missing_keys = keys - set(self.keys())
		if missing_keys:
			raise ConfigValidationError(f"Keys {missing_keys} are missing in {self._config_path}.")

	@property
	def is_read_only(self) -> bool:
		return self._read_only

	def __getattr__(self, name: str) -> Any:
		if name in self.keys():
			return self[name]
		else:
			try:
				return self.__dict__[name]
			except KeyError:
				raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

	def __setattr__(self, name: str, value: Any) -> None:
		if name in self.keys() and self._read_only:
			raise RuntimeError(f"'{type(self).__name__}' object is read-only")
		elif name in self.keys() and not self._read_only:
			self[name] = value
		elif name not in self.keys() and "_initialized" not in self.__dict__:
			self.__dict__[name] = value
		else:
			raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
