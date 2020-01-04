from threading import Thread

class BackupManager(Thread):
	def __init__(self):
		super(BackupManager, self).__init__()

	@staticmethod
	def backup():
		print("asdfasdfasdf")
		pass  # TODO: implement