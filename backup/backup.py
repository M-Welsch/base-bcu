from time import sleep
from threading import Thread

# from base.common.utils import run_external_command_as_generator
from subprocess import run, Popen, PIPE, STDOUT
def run_external_command_as_generator(command):
	p = run(command, stdout=PIPE, stderr=PIPE)
	return iter(p.stdout.splitlines, b'')


class BackupManager:
	def __init__(self, backup_config, logger):
		self._backup_config = backup_config
		self._logger = logger
		self._backup_thread = None

	def backup(self):
		self._backup_thread = BackupThread(self._backup_config["loop_interval"])
		self._backup_thread.start()


class BackupThread(Thread):
	def __init__(self, loop_interval):
		super(BackupThread, self).__init__()
		self._loop_interval = loop_interval

	def run(self):
		for line in run_external_command_as_generator(["ls", "-a"]):
			print(line)
			# show on display
			sleep(self._loop_interval)

	def terminate(self):
		# kill rsync
		raise NotImplementedError


if __name__ == "__main__":
	bm = BackupManager({"loop_interval": 1}, None)
	bm.backup()