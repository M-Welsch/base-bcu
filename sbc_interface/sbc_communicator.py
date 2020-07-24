import serial
import threading
from time import sleep
from datetime import datetime

class SBC_Communicator(threading.Thread):
	def __init__(self, hwctrl, to_SBC_queue, from_SBC_queue):
		super(SBC_Communicator, self).__init__()
		self._hwctrl = hwctrl
		self.to_SBC_queue = to_SBC_queue
		self.from_SBC_queue = from_SBC_queue
		self._serial_connection = serial.Serial()
		self._serial_connection.baudrate = 9600
		self._serial_connection.port = '/dev/ttyS2'
		self._serial_connection.timeout = 1
		self.exitflag = False

	def run(self):
		self._hwctrl.set_attiny_serial_path_to_communication()
		self._hwctrl.enable_receiving_messages_from_attiny() # necessary
		self._serial_connection.open()
		while not self.exitflag:
			for entry in self.to_SBC_queue:
				# print("working off to_SBC_queue with: {}".format(entry))
				self._serial_connection.write(entry.encode())
				self.from_SBC_queue.append(self._serial_connection.read_until()) # read response
				if self.from_SBC_queue:
					print(self.from_SBC_queue[-1])
			sleep(0.1)
			self.from_SBC_queue.append(self._serial_connection.read_until()) # read stuff that SBC sends without invitation

		print("SBC Communicator is terminating. So long and thanks for all the bytes!")
		self._hwctrl.disable_receiving_messages_from_attiny() # forgetting this may destroy the BPi's serial interface!

	def terminate(self):
		self.exitflag = True

	def send_current_timestamp(self):
		now = datetime.now()
		timestamp_for_sbc = now.strftime("%Y-%m-%d %H:%M:%S")
		self.to_SBC_queue.append("CT:{}".format(timestamp_for_sbc))

if __name__ == '__main__':
	import sys
	path_to_module = "/home/maxi"
	sys.path.append(path_to_module)
	from base.hwctrl.hwctrl import HWCTRL
	from base.common.config import Config
	from base.common.base_logging import Logger

	config = Config("/home/maxi/base/config.json")
	logger = Logger("/home/maxi/base/log")
	hardware_control = HWCTRL(config.hwctrl_config, logger)

	to_SBC_queue = []
	from_SBC_queue = []
	SBCC = SBC_Communicator(hardware_control, to_SBC_queue, from_SBC_queue)
	SBCC.start()
	while True:
		while from_SBC_queue:
			print(from_SBC_queue.pop())
		sleep(0.05)