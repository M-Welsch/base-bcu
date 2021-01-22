from queue import Queue


class Current_Queue(Queue):
	def __init__(self, maxsize):
		super(Current_Queue, self).__init__(maxsize = maxsize)

	def put_current(self, current_value):
		if self.full():
			self.get()
		self.put(current_value)