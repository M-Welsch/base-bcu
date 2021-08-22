from re import findall
from typing import Optional

from base.common.logger import LoggerFactory
from base.hardware.sbu.sbu_commands import SbuCommand, SbuCommands
from base.hardware.sbu.sbu_communicator import SbuCommunicator

LOG = LoggerFactory.get_logger(__name__)


class SBU:
    _sbu_communicator: Optional[SbuCommunicator] = None

    def __init__(self) -> None:
        if self._sbu_communicator is None:
            self._sbu_communicator = SbuCommunicator()

    def write_to_display(self, line1: str, line2: str) -> None:
        assert isinstance(self._sbu_communicator, SbuCommunicator)
        self.check_display_line_for_length(line1)
        self.check_display_line_for_length(line2)
        self._sbu_communicator.process_command(SbuCommands.write_to_display_line1, line1[:16])
        self._sbu_communicator.process_command(SbuCommands.write_to_display_line2, line2[:16])

    @staticmethod
    def check_display_line_for_length(line: str) -> None:
        if len(line) > 16:
            LOG.warning(f"Display string {line} is too long!")

    def set_display_brightness_percent(self, display_brightness_in_percent: float) -> None:
        assert isinstance(self._sbu_communicator, SbuCommunicator)
        self._sbu_communicator.process_command(
            SbuCommands.set_display_brightness, str(self._condition_brightness_value(display_brightness_in_percent))
        )

    def set_led_brightness_percent(self, led_brightness_in_percent: float) -> None:
        assert isinstance(self._sbu_communicator, SbuCommunicator)
        self._sbu_communicator.process_command(
            SbuCommands.set_led_brightness, str(self._condition_brightness_value(led_brightness_in_percent))
        )

    @staticmethod
    def _condition_brightness_value(brightness_in_percent: float) -> int:
        brightness_16bit = int(brightness_in_percent / 100 * 65535)
        maximum_brightness = 65535  # 16bit
        if brightness_16bit > maximum_brightness:
            LOG.warning(
                f"brightness value too high. Maximum is {maximum_brightness}, "
                f"however {brightness_16bit} was given. Clipping to maximum."
            )
            brightness_16bit = maximum_brightness
        elif brightness_16bit < 0:
            LOG.warning(f"Brightness shall not be negative. Clipping to zero.")
            brightness_16bit = 0
        return brightness_16bit

    def send_seconds_to_next_bu(self, seconds: int) -> None:
        assert isinstance(self._sbu_communicator, SbuCommunicator)
        command = SbuCommands.set_seconds_to_next_bu
        payload = str(int(seconds))
        LOG.info(f"Command: message_code = {command.message_code}, payload = {payload}")
        assertion_message = self._sbu_communicator.process_command(command, payload)
        value_in_cmp_register = int(findall(r"\d+", assertion_message)[0])
        LOG.info(f"value_in_cmp_register: {value_in_cmp_register}, derived from {assertion_message}")
        assert value_in_cmp_register == int(seconds / 32)

    def send_readable_timestamp(self, timestamp: str) -> None:
        assert isinstance(self._sbu_communicator, SbuCommunicator)
        self._sbu_communicator.process_command(SbuCommands.send_readable_timestamp_of_next_bu, timestamp)

    def measure_base_input_current(self) -> float:
        return self._measure(SbuCommands.measure_current)

    def measure_vcc3v_voltage(self) -> float:
        return self._measure(SbuCommands.measure_vcc3v)

    def measure_sbu_temperature(self) -> float:
        return self._measure(SbuCommands.measure_temperature)

    def _measure(self, command: SbuCommand) -> float:
        assert isinstance(self._sbu_communicator, SbuCommunicator)
        response = self._sbu_communicator.process_command(command)
        # LOG.debug(f"response is {response}")
        response_16bit_value = int(findall(r"[0-9]+", response[2:])[0])
        return self._convert_measurement_result(command, response_16bit_value)

    @staticmethod
    def _convert_measurement_result(command: SbuCommand, raw_value: int) -> Optional[float]:
        converted_value: Optional[float]
        if command.message_code == "CC":
            converted_value = raw_value * 0.00234
        elif command.message_code == "3V":
            converted_value = raw_value * 3.234 / 1008
        elif command.message_code == "TP":
            converted_value = raw_value  # Todo: implement this in sbu
        else:
            LOG.warning(f"cannot convert anything from {command.message_code} (raw value given is {raw_value})")
            converted_value = None
        return converted_value

    def request_shutdown(self) -> None:
        assert isinstance(self._sbu_communicator, SbuCommunicator)
        self._sbu_communicator.process_command(SbuCommands.request_shutdown)

    def abort_shutdown(self) -> None:
        assert isinstance(self._sbu_communicator, SbuCommunicator)
        self._sbu_communicator.process_command(SbuCommands.abort_shutdown)


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
