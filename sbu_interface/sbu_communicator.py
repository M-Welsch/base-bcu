import serial
import os
from time import sleep, time
from datetime import datetime
import re
import sys
path_to_module = "/home/maxi"
sys.path.append(path_to_module)
from base.sbu_interface.sbu_uart_finder import SbuUartFinder


class SbuCommunicator():
    def __init__(self, hwctrl, logger, config_sbuc):
        self._serial_connection = None
        self._hwctrl = hwctrl
        self._logger = logger
        self._config_sbuc = config_sbuc
        self._channel_busy = True
        self._sbu_ready = False
        self._sbuc_logfile = self._open_logfile()
        self._prepare_serial_connection()
        self._open_serial_connection()

    def _open_serial_connection(self):
        self._serial_connection = self._prepare_serial_connection()
        sbu_uart_interface = self._get_sbu_uart_interface()
        if sbu_uart_interface is None:
            print("WARNING! Serial port to SBC could not found! Display and buttons will not work!")
            self._append_to_sbu_logfile("SBU not found!")
        else:
            self._append_to_sbu_logfile(f"Opening USART interface {sbu_uart_interface}")
            self._serial_connection.port = sbu_uart_interface
            self._serial_connection.open()
            self._flush_sbu_channel()
            self._channel_busy = False
            self._sbu_ready = True

    def _prepare_serial_connection(self):
        serial_connection = serial.Serial()
        serial_connection.baudrate = 9600
        serial_connection.timeout = 1
        return serial_connection

    def _get_sbu_uart_interface(self):
        self._prepare_hardware_for_sbu_communication()
        sbu_uart_interface = SbuUartFinder(self._logger).get_sbu_uart_interface()
        return sbu_uart_interface

    def _prepare_hardware_for_sbu_communication(self):
        self._hwctrl.set_attiny_serial_path_to_communication()
        self._hwctrl.enable_receiving_messages_from_attiny()  # necessary
        
    def _open_logfile(self):
        filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + "sbu_communicator.log"
        directory = self._config_sbuc["logs_directory"]
        path = os.path.join(directory, filename)
        return open(path,"w")

    def _append_to_sbu_logfile(self, message):
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self._sbuc_logfile.write(f"{now}: {message}\n")

    def _close_logfile(self):
        self._sbuc_logfile.close()

    @property
    def is_serial_connection_open(self):
        return self._serial_connection.is_open

    @property
    def sbu_ready(self):
        return self._sbu_ready

    def _send_message_to_sbu(self, message):
        message = message + '\0'
        self._serial_connection.write(message.encode())

    def _flush_sbu_channel(self):
        self._send_message_to_sbu('\0')

    def _transfer_command_acknowledged(self, message_code, payload=""):
        self._append_to_sbu_logfile(f"Command: message_code = {message_code}, payload = {payload}")
        print(f"Command: message_code = {message_code}, payload = {payload}")
        self._send_message_to_sbu(f"{message_code}:{payload}")
        acknowledge_delay = self._wait_for_acknowledge(message_code)
        ready_delay = self._wait_for_sbu_ready()
        self._append_to_sbu_logfile(f"{message_code} acknowledged after {acknowledge_delay}s, ready after {ready_delay}")


    def _wait_for_acknowledge(self, message_code):
        time_start = time()
        timeout = 1
        while time() - time_start < timeout:
            tmp = self._serial_connection.read_until().decode()
            if f"ACK:{message_code}" in tmp:
                break
            sleep(0.05)
        return time()-time_start

    def _wait_for_sbu_ready(self):
        time_start = time()
        timeout = 1
        while time() - time_start < timeout:
            tmp = self._serial_connection.read_until().decode()
            if f"Ready" in tmp:
                break
            sleep(0.05)
        return time()-time_start

    def _wait_for_special_string(self, special_string):
        time_start = time()
        timeout = 1
        tmp = None
        while time() - time_start < timeout:
            tmp = self._serial_connection.read_until().decode()
            if special_string in tmp:
                break
            sleep(0.05)
        return [tmp, time() - time_start]

    def _wait_for_channel_free(self):
        while self._channel_busy or not self._sbu_ready:
            # print(f"waiting for sbu_channel: busy={self._channel_busy}, open={self.is_serial_connection_open:}")
            sleep(0.05)

    def terminate(self):
        print("SBC Communicator is terminating. So long and thanks for all the bytes!")
        self._serial_connection.close()
        self._hwctrl.disable_receiving_messages_from_attiny()  # forgetting this may destroy the BPi's serial interface!
        self._close_logfile()

    def send_seconds_to_next_bu_to_sbu(self, seconds):
        # Todo: cleanup this mess
        message_code = "BU"
        payload = int(seconds)
        self._append_to_sbu_logfile(f"Command: message_code = {message_code}, payload = {payload}")
        print(f"Command to SBU: {message_code}:{payload}")
        self._send_message_to_sbu(f"{message_code}:{payload}")
        acknowledge_delay = self._wait_for_acknowledge(message_code)
        [callback, callback_delay] = self._wait_for_special_string("CMP")
        ready_delay = self._wait_for_sbu_ready()
        self._append_to_sbu_logfile(f"{message_code} acknowledged after {acknowledge_delay}s, ready after {ready_delay}. Callback: {callback} after {callback_delay}s")
        print(f"{message_code} acknowledged after {acknowledge_delay}s, ready after {ready_delay}. Callback: {callback} after {callback_delay}s")


    def send_human_readable_timestamp_next_bu(self, timestamp_hr):
        self._transfer_command_acknowledged("BR",timestamp_hr)

    def write_to_display(self, line1, line2):
        self._wait_for_channel_free()
        self._channel_busy = True
        self._transfer_command_acknowledged("D1", line1)
        self._transfer_command_acknowledged("D2", line2)
        self._channel_busy = False

    def send_shutdown_request(self):
        self._transfer_command_acknowledged("SR")

    def set_display_brightness_16bit(self, display_brightness_16bit):
        display_brightness_16bit = self._condition_brightness_value(display_brightness_16bit, "display")
        self._transfer_command_acknowledged("DB",display_brightness_16bit)

    def set_display_brightness_percent(self, display_brightness_in_percent):
        display_brightness_16bit = int(display_brightness_in_percent / 100 * 65535)
        self.set_display_brightness_16bit(display_brightness_16bit)

    def set_led_brightness_16bit(self, led_brightness_16bit):
        led_brightness_16bit = self._condition_brightness_value(led_brightness_16bit, "HMI LED")
        self._transfer_command_acknowledged("DL", led_brightness_16bit)

    def set_led_brightness_percent(self, led_brightness_precent):
        led_brightness_16bit = int(led_brightness_precent / 100 * 65535)
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
        self._wait_for_channel_free()
        self._channel_busy = True
        self._transfer_command_acknowledged("CC")
        current_16bit = self._wait_for_meas_result("CC")
        self._channel_busy = False
        if current_16bit is None:
            current = None
        else:
            current = self._convert_16bit_result_to_ampere(current_16bit)
        return current

    def vcc3v_measurement(self):
        self._wait_for_channel_free()
        self._channel_busy = True
        self._transfer_command_acknowledged("3V")
        vcc3v_16bit = self._wait_for_meas_result("3V")
        self._channel_busy = False
        if vcc3v_16bit is None:
            vcc3v = None
        else:
            vcc3v = self._convert_16bit_3v_result_to_volts(vcc3v_16bit)
        return vcc3v

    def _wait_for_meas_result(self, measType):
        time_start = time()
        timeout = 2
        while time() - time_start < timeout:
            tmp = self._serial_connection.read_until('\n').decode()
            if measType in tmp:
                try:
                    meas_result_payload = tmp.split(":")[1]
                    meas_result_pattern = '[0-9]+'
                    meas_result_match = re.search(meas_result_pattern, meas_result_payload).group(0)
                    meas_result_16bit = int(meas_result_match)
                except:
                    meas_result_16bit = None
                self._append_to_sbu_logfile(f"current measurement 16 bit value: {meas_result_16bit}")
                return meas_result_16bit

    @staticmethod
    def _convert_16bit_result_to_ampere(current_measurement_16bit):
        # Fixme: do properly!
        return current_measurement_16bit * 0.00234

    @staticmethod
    def _convert_16bit_3v_result_to_volts(vcc3v_meas_result_16bit):
        # Fixme: do properly!
        return vcc3v_meas_result_16bit * 3.234 / 1008

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

    SBUC = SbuCommunicator(hardware_control, logger)
    while True:
        cc = SBUC.current_measurement()
        vcc3v = SBUC.vcc3v_measurement()
        content = [f"Iin = {cc}A", f"VCC3V = {vcc3v}V"]
        SBUC.write_to_display(content[0], content[1])
        print(content)