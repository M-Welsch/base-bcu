from schedule import Scheduler as Scheduler
from datetime import datetime

class BaseScheduler(Scheduler):
	def __init__(self, config_schedule):
		super(BaseScheduler, self).__init__()
		self._config_schedule = config_schedule
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

	def next_backup_scheduled(self):
		# returns datetime-object
		return self.next_run

	def seconds_to_next_bu(self):
		seconds_to_next_bu = self.idle_seconds
		return seconds_to_next_bu
