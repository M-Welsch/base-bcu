from time import sleep, time
from threading import Thread

# from base.common.utils import run_external_command_as_generator
from subprocess import run, Popen, PIPE, STDOUT
def run_external_command_as_generator(command):
	p = Popen(command, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True)
	return p.stdout


class BackupManager:
	def __init__(self, backup_config, logger):
		self._backup_config = backup_config
		self._logger = logger
		self._backup_thread = None

	def backup(self):
		self._backup_thread = BackupThread(self._backup_config["sample_interval"])
		self._backup_thread.start()


class BackupThread(Thread):
	def __init__(self, sample_interval):
		super(BackupThread, self).__init__()
		self._sample_interval = sample_interval

	def run(self):
		start = time()
		# for line in run_external_command_as_generator(["find", "/"]):
		for line in run_external_command_as_generator(["grep", "-r", "-i", "e", "/home"]):
			now = time()
			if now - start >= self._sample_interval:
				print(line.strip())
				# show on display
				start = now

	def terminate(self):
		# kill rsync
		raise NotImplementedError


if __name__ == "__main__":
	bm = BackupManager({"sample_interval": 0.2}, None)
	bm.backup()