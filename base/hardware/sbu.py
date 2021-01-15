import serial
import glob
import logging
from dataclasses import dataclass
from pathlib import Path
from time import time, sleep


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


class SbuCommands:
    def __init__(self):
        self.write_to_display_line1 = SbuCommand(
            message_code="D1",
            wait_for_acknowledge=True,
            wait_for_ready=True
        )
        self.write_to_display_line2 = SbuCommand(
            message_code="D2",
            wait_for_acknowledge=True,
            wait_for_ready=True
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
        self._send_message_to_sbu(f"{command.message_code}:{payload}")
        if command.wait_for_acknowledge:
            acknowledge_delay = self._wait_for_acknowledge(command.message_code)
            log_message = f"{command.message_code} with payload {payload} acknowledged after {acknowledge_delay}s"
        if command.wait_for_ready:
            ready_delay = self._wait_for_sbu_ready()
            log_message += f", ready after {ready_delay}"
        LOG.info(log_message)

    def _send_message_to_sbu(self, message):
        message = message + '\0'
        self._serial_connection.write(message.encode())

    def _wait_for_acknowledge(self, message_code) -> int:
        return self._wait_for_response(f"ACK:{message_code}")

    def _wait_for_response(self, response) -> int:
        time_start = time()
        time_diff = 0
        while True:
            time_diff = time() - time_start
            tmp = self._serial_connection.read_until().decode()
            if response in tmp:
                break
            if time_diff > self._config.wait_for_acknowledge_timeout:
                raise SbuCommunicationTimeout(f"waiting for {response} took {time_diff}")
            sleep(0.05)
        return time_diff

    # Fixme: for some reason the wait for ready loop doesnt work when included in wait_for_response
    def _wait_for_sbu_ready(self):
        time_start = time()
        while time() - time_start < self._config.wait_for_sbu_ready_timeout:
            tmp = self._serial_connection.read_until().decode()
            if f"Ready" in tmp:
                break
            sleep(0.05)
        return time() - time_start

    def write_to_display(self, line1, line2):
        self.check_display_line_for_length(line1)
        self.check_display_line_for_length(line2)
        self._process_command(self._sbu_commands.write_to_display_line1, line1)
        self._process_command(self._sbu_commands.write_to_display_line2, line2)

    def check_display_line_for_length(self, line):
        if len(line) > 16:
            LOG.warning(f"Display string {line} is too long!")


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