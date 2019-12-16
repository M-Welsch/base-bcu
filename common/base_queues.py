from queue import Queue

class LoggingQueue(Queue):
	def __init__(self):
		super(LoggingQueue, self).__init__()

	def work_off_msg(self, log_fn):
		if not self.empty():
			msg = self.get(block=False)
			log_fn(msg)
			self.task_done()

	def push_msg(self, msg):
		self.put(msg)