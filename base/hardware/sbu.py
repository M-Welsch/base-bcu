import serial
import glob
import os
import logging
from dataclasses import dataclass
from pathlib import Path
from time import time, sleep
from re import findall
from subprocess import Popen, PIPE

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
    await_acknowledge: bool
    await_ready_signal: bool
    await_response: bool = False
    response_keyword: str = ""
    automatically_free_channel: bool = True


class SbuCommands:
    write_to_display_line1 = SbuCommand(
        message_code="D1",
        await_acknowledge=True,
        await_ready_signal=False # yes, that's how it is!
    )
    write_to_display_line2 = SbuCommand(
        message_code="D2",
        await_acknowledge=True,
        await_ready_signal=True
    )
    set_display_brightness = SbuCommand(
        message_code="DB",
        await_acknowledge=True,
        await_ready_signal=True
    )
    set_led_brightness = SbuCommand(
        message_code="DL",
        await_acknowledge=True,
        await_ready_signal=True
    )
    set_seconds_to_next_bu = SbuCommand(
        message_code="BU",
        await_acknowledge=True,
        await_ready_signal=True,
        await_response=True,
        response_keyword="CMP"
    )
    send_readable_timestamp_of_next_bu = SbuCommand(
        message_code="BR",
        await_acknowledge=False,  # Fixme: SBU Bug!
        await_ready_signal=True
    )
    measure_current = SbuCommand(
        message_code="CC",
        await_acknowledge=True,
        await_ready_signal=True,
        await_response=True,
        response_keyword="CC"
    )
    measure_vcc3v = SbuCommand(
        message_code="3V",
        await_acknowledge=True,
        await_ready_signal=True,
        await_response=True,
        response_keyword="3V"
    )
    measure_temperature = SbuCommand(
        message_code="TP",
        await_acknowledge=True,
        await_ready_signal=True,
        await_response=True,
        response_keyword="TP"
    )
    request_shutdown = SbuCommand(
        message_code="SR",
        await_acknowledge=True,
        await_ready_signal=False
    )
    abort_shutdown = SbuCommand(
        message_code="SA",
        await_acknowledge=True,
        await_ready_signal=False
    )
    request_wakeup_reason = SbuCommand(
        message_code="WU",
        await_acknowledge=True,
        await_ready_signal=True,
        await_response=True,
        response_keyword="WU"
    )


class SBU:
    def __init__(self):
        self._config = Config("sbu.json")
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

    def close_serial_connection(self):
        LOG.info("SBU Communicator is terminating. So long and thanks for all the bytes!")
        self._serial_connection.close()
        self._pin_interface.disable_receiving_messages_from_sbu()

    def _flush_sbu_channel(self):
        self._send_message_to_sbu('\0')

    def _process_command(self, command: SbuCommand, payload=""):
        log_message = ""
        sbu_response = None
        self._wait_for_channel_free()
        self._channel_busy = True
        try:
            self._send_message_to_sbu(f"{command.message_code}:{payload}")
            if command.await_acknowledge:
                [acknowledge_delay, _] = self._await_acknowledge(command.message_code)
                log_message = f"{command.message_code} with payload {payload} acknowledged after {acknowledge_delay}s"
            if command.await_response:
                [response_delay, sbu_response] = self._wait_for_response(command.response_keyword)
                log_message += f", special string received after {response_delay}"
            if command.await_ready_signal:
                [ready_delay, _] = self._wait_for_sbu_ready()
                log_message += f", ready after {ready_delay}"
            LOG.info(log_message)
        except SbuCommunicationTimeout as e:
            LOG.error(e)
            self._flush_sbu_channel()
        finally:
            if command.automatically_free_channel:
                self._channel_busy = False
        return sbu_response

    def _wait_for_channel_free(self):
        time_start = time()
        while self._channel_busy or not self._sbu_ready:
            sleep(0.05)
            if time() - time_start > self._config.wait_for_channel_free_timeout:
                raise SbuCommunicationTimeout(
                    f'Waiting for longer than {self._config.wait_for_channel_free_timeout} '
                    f'for channel to be free.'
                )

    def _send_message_to_sbu(self, message):
        message = message + '\0'
        self._serial_connection.write(message.encode())

    def _await_acknowledge(self, message_code) -> int:
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
            if time_diff > self._config.sbu_response_timeout:
                raise SbuCommunicationTimeout(f"waiting for {response} took {time_diff}")
        return [time_diff, tmp]

    def write_to_display(self, line1, line2):
        self.check_display_line_for_length(line1)
        self.check_display_line_for_length(line2)
        self._process_command(SbuCommands.write_to_display_line1, line1)
        self._process_command(SbuCommands.write_to_display_line2, line2)

    @staticmethod
    def check_display_line_for_length(line):
        if len(line) > 16:
            LOG.warning(f"Display string {line} is too long!")

    def set_display_brightness_percent(self, display_brightness_in_percent):
        self._process_command(SbuCommands.set_display_brightness,
                              self._condition_brightness_value(display_brightness_in_percent))

    def set_led_brightness_percent(self, led_brightness_in_percent):
        self._process_command(SbuCommands.set_led_brightness,
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
        command = SbuCommands.set_seconds_to_next_bu
        payload = int(seconds)
        LOG.info(f"Command: message_code = {command.message_code}, payload = {payload}")
        assertion_message = self._process_command(command, payload)
        value_in_cmp_register = int(findall(r'\d+', assertion_message)[0])
        assert value_in_cmp_register == int(seconds/32)

    def send_readable_timestamp(self, timestamp):
        self._process_command(SbuCommands.send_readable_timestamp_of_next_bu, timestamp)

    def measure_base_input_current(self) -> float:
        return self._measure(SbuCommands.measure_current)

    def measure_vcc3v_voltage(self) -> float:
        return self._measure(SbuCommands.measure_vcc3v)

    def measure_sbu_temperature(self) -> float:
        return self._measure(SbuCommands.measure_temperature)

    def _measure(self, command: SbuCommand) -> float:
        response = self._process_command(command)
        print(f"response is {response}")
        response_16bit_value = int(findall(r'[0-9]+', response[2:])[0])
        return self._convert_measurement_result(command, response_16bit_value)

    @staticmethod
    def _convert_measurement_result(command: SbuCommand, raw_value: int) -> float:
        if command.message_code == "CC":
            converted_value = raw_value * 0.00234
        elif command.message_code == "3V":
            converted_value = raw_value * 3.234 / 1008
        elif command.message_code == "TP":
            raise NotImplementedError("Temperature Measurement lacks implementation on SBU side!")
        else:
            LOG.warning(f"cannot convert anything from {command.message_code} (raw value given is {raw_value})")
            converted_value = None
        return converted_value

    def request_shutdown(self):
        self._process_command(SbuCommands.request_shutdown)

    def abort_shutdown(self):
        self._process_command(SbuCommands.abort_shutdown)


class SbuUartFinder:
    def get_sbu_uart_interface(self) -> str:
        uart_interfaces = self._get_available_uart_interfaces()
        uart_sbu = self._test_uart_interfaces_for_echo(uart_interfaces)
        if uart_sbu:
            LOG.info("SBU answers on UART Interface {}".format(uart_sbu))
        else:
            LOG.error("SBU doesn't respond on any UART Interface!")
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
            return False
        else:
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


class SbuUpdater:
    # Todo: cleanup
    def __init__(self):
        self._pin_interface = PinInterface.global_instance()

    def update(self, sbu_fw_filename=""):
        self._pin_interface.set_sbu_serial_path_to_communication()
        self._pin_interface.enable_receiving_messages_from_sbu()
        sbu_uart_channel = self._get_sbu_uart_channel()
        self._pin_interface.set_sbu_serial_path_to_sbu_fw_update()
        if not sbu_fw_filename:
            sbu_fw_filename = self._get_filename_of_newest_hex_file()
        self._execute_sbu_update(sbu_fw_filename, sbu_uart_channel)

    def _execute_sbu_update(self, sbu_fw_filename, sbu_uart_channel):
        sbu_update_command = f'sudo su - base -c "pyupdi -d tiny816 -c {sbu_uart_channel} -f {sbu_fw_filename}"'
        try:
            process = Popen(sbu_update_command,
                            bufsize=0,
                            shell=True,
                            universal_newlines=True,
                            stdout=PIPE,
                            stderr=PIPE)
            for line in process.stdout:
                LOG.info(line)
            if process.stderr:
                LOG.error(process.stderr)
        finally:
            self._pin_interface.set_sbu_serial_path_to_communication()

    @staticmethod
    def _get_sbu_uart_channel():
        sbu_uart_channel = SbuUartFinder().get_sbu_uart_interface()
        if not sbu_uart_channel:
            sbu_uart_channel = "/dev/ttyS1"
        return sbu_uart_channel

    @staticmethod
    def _get_filename_of_newest_hex_file():
        list_of_sbc_fw_files = glob.glob("/home/base/python.base/sbu_fw_files/*")
        latest_sbc_fw_file = max(list_of_sbc_fw_files, key=os.path.getctime)
        return latest_sbc_fw_file


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
