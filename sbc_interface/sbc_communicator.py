import serial
import threading
from time import sleep, time
from datetime import datetime
from queue import Queue
import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)
from base.sbc_interface.sbc_uart_finder import SbcUartFinder


class SbcCommunicator(threading.Thread):
    def __init__(self, hwctrl, logger):
        super(SbcCommunicator, self).__init__()
        self._hwctrl = hwctrl
        self._logger = logger
        self._from_SBC_queue = Queue()
        self._to_sbc_queue = Queue()
        self._flush_to_sbc_queue()
        self._exitflag = False
        self._serial_connection = self._prepare_serial_connection()

    def _prepare_serial_connection(self):
        serial_connection = serial.Serial()
        serial_connection.baudrate = 9600
        serial_connection.timeout = 1
        return serial_connection

    @property
    def is_serial_connection_open(self):
        return self._serial_connection.is_open()

    def _flush_to_sbc_queue(self):
        self.append_to_sbc_communication_queue('\0')

    def _get_uart_line_to_sbc(self):
        self._prepare_hardware_for_sbu_communication()
        uart_line_to_sbc = SbcUartFinder(self._logger).get_uart_line_to_sbc()
        # print(uart_line_to_sbc)
        return uart_line_to_sbc

    def _prepare_hardware_for_sbu_communication(self):
        self._hwctrl.set_attiny_serial_path_to_communication()
        self._hwctrl.enable_receiving_messages_from_attiny()  # necessary

    def run(self):
        uart_line_to_sbc = self._get_uart_line_to_sbc()
        if uart_line_to_sbc == None:
            print("WARNING! Serial port to SBC could not found! Display and buttons will not work!")
        else:
            self._serial_connection.port = uart_line_to_sbc
            self._serial_connection.open()
            while not self._exitflag:
                if not self._to_sbc_queue.empty():
                    entry = self._to_sbc_queue.get()
                    entry = self._check_for_line_ending(entry, "report")
                    print("working off to_SBC_queue with: {}".format(entry))
                    self._serial_connection.write(entry.encode())
                    self._from_SBC_queue.put(self._serial_connection.read_until())  # read response
                sleep(0.1)
                self._from_SBC_queue.put(self._serial_connection.read_until())  # read stuff that SBC sends without invitation

            self._serial_connection.close()
            print("SBC Communicator is terminating. So long and thanks for all the bytes!")
            self._hwctrl.disable_receiving_messages_from_attiny()  # forgetting this may destroy the BPi's serial interface!

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
        self._exitflag = True

    def _wait_for_queues_to_empty(self):
        start = time()
        timediff = 0
        while not self._to_sbc_queue.empty() and timediff < 2:
            timediff = time() - start
            sleep(0.1)

    def send_seconds_to_next_bu_to_sbc(self, seconds):
        amount_32_sec_packages = seconds/32
        self.append_to_sbc_communication_queue("BU:{}\0".format(amount_32_sec_packages))

    def write_to_display(self, line1, line2):
        self.append_to_sbc_communication_queue("D1:{}\0".format(line1))
        self.append_to_sbc_communication_queue("D2:{}\0".format(line2))

    def send_shutdown_request(self):
        self.append_to_sbc_communication_queue("SR:\n")

    def set_display_brightness_16bit(self, display_brightness_16bit):
        display_brightness_16bit = self._condition_brightness_value(display_brightness_16bit, "display")
        self.append_to_sbc_communication_queue(f"DB:{display_brightness_16bit}\n")

    def set_display_brightness_percent(self, display_brightness_in_percent):
        display_brightness_16bit = display_brightness_in_percent / 100 * 65535
        self.set_display_brightness_16bit(display_brightness_16bit)

    def set_led_brightness_16bit(self, led_brightness_16bit):
        led_brightness_16bit = self._condition_brightness_value(led_brightness_16bit, "HMI LED")
        self.append_to_sbc_communication_queue("LB:{led_brightness_16bit}\n")

    def set_led_brightness_percent(self, led_brightness_precent):
        led_brightness_16bit = led_brightness_precent / 100 * 65535
        self.set_led_brightness_16bit(led_brightness_16bit)

    def _condition_brightness_value(self, brightness_16bit, brightness_type):
        maximum_brightness = 65535  # 16bit
        if not type(brightness_16bit) == int:
            warning_msg = f"wrong datatype for {brightness_type}_brighness_16bit. It has to be integer, however it is {type(brightness_16bit)}"
            print(warning_msg)
            self._logger.warning(warning_msg)
            brightness_16bit = int(brightness_16bit)
        if brightness_16bit > maximum_brightness:
            warning_msg = f"{brightness_type} brightness value too high. Maximum is {maximum_brightness}, however {brightness_16bit} was given. Clipping to maximum."
            print(warning_msg)
            self._logger.warning(warning_msg)
            brightness_16bit = maximum_brightness
        elif brightness_16bit < 0:
            warning_msg = f"{brightness_type} Brightness shall not be negative. Clipping to zero."
            print(warning_msg)
            self._logger.warning(warning_msg)
            brightness_16bit = 0
        return brightness_16bit

    def current_measurement(self):
        self.append_to_sbc_communication_queue("CC{}\0")

        return current_in_Ampere

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

    SBCC = SbcCommunicator(hardware_control, logger)
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