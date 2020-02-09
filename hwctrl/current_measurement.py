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
		self._flag_measurement_series_running = False

	def run(self):
		self._exit_flag = False
		while not self._exit_flag: 
			data = self._bus.read_i2c_block_data(0x4d,1) # reads lower byte first
			self._current = data[0] * 255 + data[1]
			self._current_q.put_current(self._current)
			if self.current > self._peak_current: self._peak_current = self._current
			self.process_measurement_series()
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

	def start_measurements_series(self, amount_of_measurements):
		self._flag_measurement_series_running = True
		self._current_q_for_measurement_series = Current_Queue(maxsize = amount_of_measurements)

	def process_measurement_series(self):
		if self._flag_measurement_series_running:
			self.add_measurement_to_series()

	def add_measurement_to_series(self):
		if self._current_q_for_measurement_series.full():
			self._flag_measurement_series_running = False

		if self._flag_measurement_series_running:
			self._current_q_for_measurement_series.put(self._current)

	@property
	def flag_measurement_series_running(self):
		return self._flag_measurement_series_running

	@property
	def current_series(self):
		while not self._current_q_for_measurement_series.empty():
			current_series.append(self._current_q_for_measurement_series.get())
		return current_series

	def terminate(self):
		self._exit_flag = True