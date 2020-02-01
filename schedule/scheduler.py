from schedule import Scheduler as Scheduler

class BaseScheduler(Scheduler):
	def __init__(self):
		super(BaseScheduler, self).__init__()
		self.backup_suggested = False
		self.setup_schedule()

	def setup_schedule(self):
		self.every(1000).seconds.do(self._suggest_backup)

	def _suggest_backup(self):
		print("Suggesting backup...")
		self.backup_suggested = True
	
	def is_backup_scheduled(self):
		self.run_pending()
		result = self.backup_suggested
		return result