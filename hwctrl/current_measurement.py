import smbus
from threading import Thread
from time import sleep
from base.common.base_queues import Current_Queue

class Current_Measurement(Thread):
	def __init__(self, sampling_interval):
		print("Current Sensor is initializing")
		super(Current_Measurement, self).__init__()
		self._samling_interval = sampling_interval
		self._bus = smbus.SMBus(1)
		self._exit_flag = False
		self._peak_current = 0
		self._current = 0
		self._current_q = Current_Queue(maxsize=100)

	def run(self):
		self._exit_flag = False
		while not self._exit_flag: 
			data = self._bus.read_i2c_block_data(0x4d,1)
			self._current = int(str(data[0]) + str(data[1]))
			self._current_q.put_current(self._current)
			if self.current > self._peak_current: self._peak_current = self._current
			sleep(self._samling_interval)

	@property
	def current(self):
		return self._current

	@property
	def peak_current(self):
		return self._peak_current

	@property
	def avg_current_10sec(self):
		qsize = self._current_q.qsize()
		avg_current_10sec = 0
		while not self._current_q.empty():
			avg_current_10sec = avg_current_10sec + self._current_q.get()
		avg_current_10sec = avg_current_10sec / qsize
		return avg_current_10sec
	
	def terminate(self):
		self._exit_flag = True