import os, sys, glob, serial

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)


class SbuUartFinder:
    def __init__(self, logger):
        self._logger = logger

    def get_sbu_uart_interface(self):
        uart_interfaces = self._get_available_uart_interfaces()
        uart_sbc = self._test_uart_interfaces_for_echo(uart_interfaces)
        if uart_sbc:
            self._logger.info("SBC answers on UART Interface {}".format(uart_sbc))
        else:
            self._logger.warning("SBC doesn't respond on any UART Interface!")
        return uart_sbc

    @staticmethod
    def _get_available_uart_interfaces():
        return glob.glob("/dev/ttyS*")

    def _test_uart_interfaces_for_echo(self, uart_interfaces):
        sbu_uart_interface = None
        for uart_interface in uart_interfaces:
            if self._test_uart_interface_for_echo(uart_interface):
                sbu_uart_interface = uart_interface
        return sbu_uart_interface

    @staticmethod
    def _test_uart_interface_for_echo(uart_interface):
        try:
            response = SbuUartFinder._challenge_interface(uart_interface)
        except serial.SerialException:
            print("{} could not be opened".format(uart_interface))
            return False
        else:
            print(f"Challanged {uart_interface}, responded {response}.")
            return response.endswith(b"Echo")

    @staticmethod
    def _challenge_interface(uart_interface):
        with serial.Serial(uart_interface, 9600, timeout=1) as ser:
            ser.reset_input_buffer()
            ser.write(b'\0')
            ser.write(b"Test\0")
            response = ser.read_until(b"Echo")
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        return response


if __name__ == "__main__":
    from base.common.config import Config
    from base.common.base_logging import Logger
    from base.hwctrl.hwctrl import *

    _config = Config("/home/maxi/base/config.json")
    _logger = Logger("/home/maxi/base/log")
    _hardware_control = HWCTRL(_config.hwctrl_config, _logger)
    _hardware_control.set_attiny_serial_path_to_communication()
    _hardware_control.enable_receiving_messages_from_attiny()

    sbc_uart_finder = SbcUartFinder(_logger)
    uart_sbc = sbc_uart_finder.get_uart_line_to_sbc()
    print(uart_sbc)
    #_hardware_control.disable_receiving_messages_from_attiny()
    #_hardware_control.set_attiny_serial_path_to_sbc_fw_update()
    _hardware_control.terminate()
    _logger.terminate()
