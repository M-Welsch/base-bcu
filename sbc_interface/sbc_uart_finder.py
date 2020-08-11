import os, sys, glob, serial

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

class SBC_UART_Finder():
	def __init__(self, logger):
		self._logger = logger

	def get_uart_line_to_sbc(self):
		uart_interfaces = self._get_available_uart_interfaces()
		uart_sbc = self._test_uart_interfaces_for_echo(uart_interfaces)
		if uart_sbc:
			self._logger.info("SBC answers on UART Interface {}".format(uart_sbc))
		else:
			self._logger.warning("SBC doesn't respond on any UART Interface!")
		# self._prepare_uart_sbc_for_fw_update(uart_sbc)
		return uart_sbc

	def _get_available_uart_interfaces(self):
		uart_interfaces = glob.glob('/dev/ttyS*')
		return uart_interfaces

	def _test_uart_interfaces_for_echo(self, uart_interfaces):
		for uart_interface in uart_interfaces:
			echo = self._test_uart_interface_for_echo(uart_interface)
			if echo:
				return uart_interface
		return None

	def _test_uart_interface_for_echo(self, uart_interface):
		try:
			with serial.Serial(uart_interface, 9600, timeout = 1) as ser:
				ser.write(b'Test\0')
				response = ser.read_until(b'Echo')
				ser.reset_input_buffer()
				ser.reset_output_buffer()
				ser.close()
		except serial.SerialException as e:
			print("{} could not be opened".format(uart_interface))
			return False

		if response[-4:] == b'Echo':
			return True
		else:
			return False

	def _prepare_uart_sbc_for_fw_update(self, sbc_interface):
		with serial.Serial(sbc_interface, 9600, parity=serial.PARITY_EVEN, timeout=1, stopbits=serial.STOPBITS_TWO) as ser:
			ser.close()


if __name__ == '__main__':
	from base.common.config import Config
	from base.common.base_logging import Logger
	from base.hwctrl.hwctrl import *

	_config = Config("/home/maxi/base/config.json")
	_logger = Logger("/home/maxi/base/log")
	_hardware_control = HWCTRL(_config.hwctrl_config, _logger)
	_hardware_control.set_attiny_serial_path_to_communication()
	_hardware_control.enable_receiving_messages_from_attiny()

	sbc_uart_finder = SBC_UART_Finder(_logger)
	uart_sbc = sbc_uart_finder.get_uart_line_to_sbc()
	print(uart_sbc)
	_hardware_control.disable_receiving_messages_from_attiny()
	_hardware_control.set_attiny_serial_path_to_sbc_fw_update()
	_hardware_control.terminate()
	_logger.terminate()