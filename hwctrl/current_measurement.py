from threading import Thread
from time import sleep
from base.common.base_queues import Current_Queue
try:
	import smbus
except ImportError:
	print("smbus not found. Using mockup.")
	

class Current_Measurement(Thread):
	def __init__(self, sampling_interval):
		print("Current Sensor is initializing")
		super(Current_Measurement, self).__init__()
		self._samling_interval = sampling_interval
		self._bus = smbus.SMBus(1)
		self._exit_flag = False
		self._peak_current = 0
		self._adc_data = 0
		self._current = 0
		self._current_q = Current_Queue(maxsize=100)

	def run(self):
		self._exit_flag = False
		while not self._exit_flag: 
			self._current = self.measure_current()
			self._current_q.put_current(self._current)
			if self.current > self._peak_current: self._peak_current = self._current
			sleep(self._samling_interval)

	def measure_current(self):
		self._adc_data = self.readout_adc_value()
		return self.convert_digits_to_mA(self._adc_data)

	def readout_adc_value(self):
		data = self._bus.read_i2c_block_data(0x4d,1) # reads lower byte first
		return data[0] * 255 + data[1]

	def convert_digits_to_mA(self, data):
		m = 0.6135218338488713
		t = -9.57712575784224
		return m * data + t

	@property
	def current(self):
		return self._current

	@property
	def adc_data(self):
		return self._adc_data

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