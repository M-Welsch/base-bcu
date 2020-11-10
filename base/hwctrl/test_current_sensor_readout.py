import sys, os
import smbus
from threading import Thread

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)


from base.hwctrl.hw_definitions import *
from base.hwctrl.current_measurement import Current_Measurement
from base.hwctrl.lcd import *

class TestI2C(Thread):
	def __init__(self):
		super(TestI2C, self).__init__()
		self.pin_interface = PinInterface(100)
		self._bus = smbus.SMBus(1)
		self._exit_flag = False
		self.cur_meas = Current_Measurement(0.1)
		self.cur_meas.start()

	def activate_current_flow(self):
		self.pin_interface.activate_hdd_pin()

	def deactivate_current_flow(self):
		self.pin_interface.deactivate_hdd_pin()

	def run(self):
		self.activate_current_flow()
		while not self._exit_flag:
			sample = self.cur_meas.current
			print("{:.2f}mA".format(sample))
			sleep(0.5)
		self.deactivate_current_flow()

	def readout_adc_low_level(self):
		data = self._bus.read_i2c_block_data(0x4d,1) # reads lower byte first
		sample = data[0] * 255 + data[1]

	def terminate(self):
		self.cur_meas.terminate()
		self._exit_flag = True

T = TestI2C()
T.start()
input("press anything to exit")
T.terminate()