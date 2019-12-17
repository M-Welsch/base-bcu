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

class Current_Queue(Queue):
	def __init__(self, maxsize):
		super(Current_Queue, self).__init__(maxsize = maxsize)

	def put_current(self, current_value):
		if self.full():
			self.get()
		self.put(current_value)