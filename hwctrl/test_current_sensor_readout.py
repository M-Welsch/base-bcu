import smbus
from time import sleep
from threading import Thread

class TestI2C(Thread):
	def __init__(self):
		super(TestI2C, self).__init__()
		self._bus = smbus.SMBus(1)
		self._exit_flag = False

	def run(self):
		while not self._exit_flag:
			data = self._bus.read_i2c_block_data(0x4d,1) # reads lower byte first
			sample = data[0] * 255 + data[1]
			print(sample)
			sleep(0.5)

	def terminate(self):
		self._exit_flag = True

T = TestI2C()
T.start()
input("press anything to exit")
T.terminate()