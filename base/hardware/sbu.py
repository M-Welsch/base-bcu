import serial
import glob
import logging
from dataclasses import dataclass
from pathlib import Path
from time import time, sleep
from re import findall

import pytest

from base.hardware.pin_interface import PinInterface
from base.common.config import Config
from base.common.exceptions import SbuCommunicationTimeout

LOG = logging.getLogger(Path(__file__).name)


@dataclass
class CommFlags:
    channel_busy: bool
    sbu_ready: bool


@dataclass
class SbuCommand:
    message_code: str
    wait_for_acknowledge: bool
    wait_for_ready: bool
    wait_for_special_string: bool=False
    special_string: str=""


class SbuCommands:
    def __init__(self):
        self.write_to_display_line1 = SbuCommand(
            message_code="D1",
            wait_for_acknowledge=True,
            wait_for_ready=False # yes, that's how it is!
        )
        self.write_to_display_line2 = SbuCommand(
            message_code="D2",
            wait_for_acknowledge=True,
            wait_for_ready=True
        )
        self.set_display_brightness = SbuCommand(
            message_code="DB",
            wait_for_acknowledge=True,
            wait_for_ready=True
        )
        self.set_led_brightness = SbuCommand(
            message_code="DL",
            wait_for_acknowledge=True,
            wait_for_ready=True
        )
        self.set_seconds_to_next_bu = SbuCommand(
            message_code="BU",
            wait_for_acknowledge=True,
            wait_for_ready=True,
            wait_for_special_string=True,
            special_string="CMP"
        )
        self.send_readable_timestamp_of_next_bu = SbuCommand(
            message_code="BR",
            wait_for_acknowledge=False, # Fixme: SBU Bug!
            wait_for_ready=True,
        )
        self.measure_current = SbuCommand(
            message_code="CC",
            wait_for_acknowledge=True,
            wait_for_ready=True,
        )
        self.measure_vcc3v = SbuCommand(
            message_code="3V",
            wait_for_acknowledge=True,
            wait_for_ready=True,
        )
        self.measure_temperature = SbuCommand(
            message_code="TP",
            wait_for_acknowledge=True,
            wait_for_ready=True,
        )


class SBU:
    def __init__(self):
        self._config = Config("sbu.json")
        self._sbu_commands = SbuCommands()
        self._pin_interface = PinInterface.global_instance()
        self._serial_connection = None
        self._init_serial_interface()

    def _init_serial_interface(self):
        self._connect_serial_communication_path()
        self._prepare_serial_connection()
        self._open_serial_connection()

    def _connect_serial_communication_path(self):
        self._pin_interface.set_sbu_serial_path_to_communication()
        self._pin_interface.enable_receiving_messages_from_sbu()

    def _prepare_serial_connection(self):
        self._serial_connection = serial.Serial()
        self._serial_connection.baudrate = 9600
        self._serial_connection.timeout = 1

    def _open_serial_connection(self):
        sbu_uart_interface = SbuUartFinder().get_sbu_uart_interface()
        if sbu_uart_interface is None:
            LOG.warning("WARNING! Serial port to SBC could not found! Display and buttons will not work!")
        else:
            LOG.info(f"SBU answered on {sbu_uart_interface}")
            self._serial_connection.port = sbu_uart_interface
            self._serial_connection.open()
            self._flush_sbu_channel()
            self._channel_busy = False
            self._sbu_ready = True

    def _flush_sbu_channel(self):
        self._send_message_to_sbu('\0')

    def _process_command(self, command: SbuCommand, payload):
        log_message = ""
        confirmation_message = None
        self._send_message_to_sbu(f"{command.message_code}:{payload}")
        if command.wait_for_acknowledge:
            [acknowledge_delay, _] = self._wait_for_acknowledge(command.message_code)
            log_message = f"{command.message_code} with payload {payload} acknowledged after {acknowledge_delay}s"
        if command.wait_for_special_string:
            [special_string_delay, confirmation_message] = self._wait_for_response(command.special_string)
            log_message += f", special string received after {special_string_delay}"
        if command.wait_for_ready:
            [ready_delay, _] = self._wait_for_sbu_ready()
            log_message += f", ready after {ready_delay}"
        LOG.info(log_message)
        return confirmation_message

    def _send_message_to_sbu(self, message):
        message = message + '\0'
        self._serial_connection.write(message.encode())

    def _wait_for_acknowledge(self, message_code) -> int:
        return self._wait_for_response(f"ACK:{message_code}")

    def _wait_for_sbu_ready(self):
        return self._wait_for_response(f"Ready")

    def _wait_for_response(self, response) -> int:
        time_start = time()
        while True:
            time_diff = time() - time_start
            tmp = self._serial_connection.read_until().decode()
            if response in tmp:
                break
            if time_diff > self._config.wait_for_acknowledge_timeout:
                raise SbuCommunicationTimeout(f"waiting for {response} took {time_diff}")
        return [time_diff, tmp]

    def write_to_display(self, line1, line2):
        self.check_display_line_for_length(line1)
        self.check_display_line_for_length(line2)
        self._process_command(self._sbu_commands.write_to_display_line1, line1)
        self._process_command(self._sbu_commands.write_to_display_line2, line2)

    @staticmethod
    def check_display_line_for_length(line):
        if len(line) > 16:
            LOG.warning(f"Display string {line} is too long!")

    def set_display_brightness_percent(self, display_brightness_in_percent):
        self._process_command(self._sbu_commands.set_display_brightness,
                              self._condition_brightness_value(display_brightness_in_percent))

    def set_led_brightness_percent(self, led_brightness_in_percent):
        self._process_command(self._sbu_commands.set_led_brightness,
                              self._condition_brightness_value(led_brightness_in_percent))

    @staticmethod
    def _condition_brightness_value(brightness_in_percent):
        brightness_16bit = int(brightness_in_percent / 100 * 65535)
        maximum_brightness = 65535  # 16bit
        if brightness_16bit > maximum_brightness:
            LOG.warning(f"brightness value too high. Maximum is {maximum_brightness}, " \
                        f"however {brightness_16bit} was given. Clipping to maximum.")
            brightness_16bit = maximum_brightness
        elif brightness_16bit < 0:
            LOG.warning(f"Brightness shall not be negative. Clipping to zero.")
            brightness_16bit = 0
        return brightness_16bit

    def send_seconds_to_next_bu(self, seconds):
        command = self._sbu_commands.set_seconds_to_next_bu
        payload = int(seconds)
        LOG.info(f"Command: message_code = {command.message_code}, payload = {payload}")
        assertion_message = self._process_command(command, payload)
        value_in_cmp_register = int(findall(r'\d+', assertion_message)[0])
        assert value_in_cmp_register == int(seconds/32)

    def send_readable_timestamp(self, timestamp):
        self._process_command(self._sbu_commands.send_readable_timestamp_of_next_bu, timestamp)

    def measure_base_input_current(self):
        self._measure(self._sbu_commands.measure_current)

    def _measure(self, command):
        pass



class SbuUartFinder:
    def get_sbu_uart_interface(self) -> str:
        uart_interfaces = self._get_available_uart_interfaces()
        uart_sbu = self._test_uart_interfaces_for_echo(uart_interfaces)
        if uart_sbu:
            LOG.info("SBU answers on UART Interface {}".format(uart_sbu))
        else:
            LOG.warning("SBU doesn't respond on any UART Interface!")
        return uart_sbu

    @staticmethod
    def _get_available_uart_interfaces() -> list:
        return glob.glob("/dev/ttyS*")

    def _test_uart_interfaces_for_echo(self, uart_interfaces):
        sbu_uart_interface = None
        for uart_interface in uart_interfaces:
            if self._test_uart_interface_for_echo(uart_interface):
                sbu_uart_interface = uart_interface
                break
        return sbu_uart_interface

    @staticmethod
    def _test_uart_interface_for_echo(uart_interface) -> bool:
        try:
            response = SbuUartFinder._challenge_interface(uart_interface)
        except serial.SerialException:
            # print("{} could not be opened".format(uart_interface))
            return False
        else:
            # print(f"Challanged {uart_interface}, responded {response}.")
            return response.endswith(b"Echo")

    @staticmethod
    def _challenge_interface(uart_interface) -> bytes:
        with serial.Serial(uart_interface, 9600, timeout=1) as ser:
            ser.reset_input_buffer()
            ser.write(b'\0')
            ser.write(b"Test\0")
            response = ser.read_until(b"Echo")
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        return response


"""
Kommandoschicht
- write to display
- set display brightness
- set led brightness
--------------------------
- set next backup time
- set readable backup timestamp
--------------------------
- measure current
- measure vcc3v
- measure temperature
--------------------------
- request shutdown
- terminate serial connection


Protokollschicht
"""
