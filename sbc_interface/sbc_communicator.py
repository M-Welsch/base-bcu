import serial
import threading
from time import sleep, time
from datetime import datetime
from queue import Queue
import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)
from base.sbc_interface.sbc_uart_finder import SBC_UART_Finder

class SBC_Communicator(threading.Thread):
	def __init__(self, hwctrl, logger):
		super(SBC_Communicator, self).__init__()
		self._hwctrl = hwctrl
		self._logger = logger
		self._from_SBC_queue = Queue()
		self._to_sbc_queue = Queue()
		self._serial_connection = serial.Serial()
		self._serial_connection.port = self._get_uart_line_to_sbc()
		self._serial_connection.baudrate = 9600
		self._serial_connection.timeout = 1
		self._flush_to_sbc_queue()
		self.exitflag = False

	def _flush_to_sbc_queue(self):
		self.append_to_sbc_communication_queue('\0')

	def _get_uart_line_to_sbc(self):
		self._hwctrl.set_attiny_serial_path_to_communication()
		self._hwctrl.enable_receiving_messages_from_attiny()
		sbc_uart_finder = SBC_UART_Finder(self._logger)
		uart_line_to_sbc = sbc_uart_finder.get_uart_line_to_sbc()
		self._hwctrl.disable_receiving_messages_from_attiny()
		self._hwctrl.set_attiny_serial_path_to_sbc_fw_update()
		print(uart_line_to_sbc)
		return uart_line_to_sbc

	def run(self):
		self._hwctrl.set_attiny_serial_path_to_communication()
		self._hwctrl.enable_receiving_messages_from_attiny() # necessary
		self._serial_connection.open()
		while not self.exitflag:
			if not self._to_sbc_queue.empty():
				entry = self._to_sbc_queue.get()
				entry = self._check_for_line_ending(entry, "report")
				print("working off to_SBC_queue with: {}".format(entry))
				self._serial_connection.write(entry.encode())
				self._from_SBC_queue.put(self._serial_connection.read_until()) # read response
			sleep(0.1)
			self._from_SBC_queue.put(self._serial_connection.read_until()) # read stuff that SBC sends without invitation

		self._serial_connection.close()
		print("SBC Communicator is terminating. So long and thanks for all the bytes!")
		self._hwctrl.disable_receiving_messages_from_attiny() # forgetting this may destroy the BPi's serial interface!

	def append_to_sbc_communication_queue(self, new_entry):
		self._to_sbc_queue.put(new_entry)

	def get_messages_from_sbc(self):
		messages_from_sbc = []
		while not self._from_SBC_queue.empty():
			messages_from_sbc.append(self._from_SBC_queue.get())
		return messages_from_sbc

	def _check_for_line_ending(self, entry, mode):
		if not entry[-1:] == '\0':
			if mode == 'strict':
				raise Exception
			if mode == 'report':
				print("line ending added to message to sbc: {}".format(entry))
			entry = entry + '\0'
		return entry

	def terminate(self):
		self._wait_for_queues_to_empty()
		self.exitflag = True

	def _wait_for_queues_to_empty(self):
		start = time()
		timediff = 0
		while not self._to_sbc_queue.empty() and timediff < 2:
			timediff = time() - start
			sleep(0.1)

	def send_seconds_to_next_bu_to_sbc(self, seconds):
		self.append_to_sbc_communication_queue("BU:{}\0".format(seconds))

	def write_to_display(self, line1, line2):
		self.append_to_sbc_communication_queue("D1:{}\0".format(line1))
		self.append_to_sbc_communication_queue("D2:{}\0".format(line2))

	def send_shutdown_request(self):
		self.append_to_sbc_communication_queue("SR:")

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

	SBCC = SBC_Communicator(hardware_control, logger)
	SBCC.start()
	testcounter = 0
	while True:
		messages_from_sbc = SBCC.get_messages_from_sbc()
		while messages_from_sbc:
			print(messages_from_sbc.pop())
		sleep(1)
		SBCC.append_to_sbc_communication_queue("D1:Test{}".format(testcounter))
		SBCC.append_to_sbc_communication_queue("D2:Test{}".format(testcounter+1))
		testcounter += 1