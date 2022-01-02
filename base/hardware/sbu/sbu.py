from enum import Enum
from re import findall
from typing import Callable, Dict, Optional

from base.common.logger import LoggerFactory
from base.hardware.sbu.commands import SbuCommand, SbuCommands
from base.hardware.sbu.communicator import SbuCommunicator

LOG = LoggerFactory.get_logger(__name__)


_sbu_measurement_data_conversion_map: Dict[str, Callable[[float], float]] = {
    "CC": lambda raw_value: raw_value * 0.00234,
    "3V": lambda raw_value: raw_value * 3.234 / 1008,
    "TP": lambda raw_value: float(raw_value),  # Todo: implement this in sbu
}


class WakeupReason(Enum):
    BACKUP_NOW = "WR_BACKUP"
    CONFIGURATION = "WR_CONFIG"
    HEARTBEAT_TIMEOUT = "WR_HB_TIMEOUT"
    NO_REASON = ""


class SBU:
    def __init__(self, sbu_communicator: SbuCommunicator) -> None:
        self._sbu_communicator = sbu_communicator

    def request_wakeup_reason(self) -> WakeupReason:
        wakeup_reason_code = self._sbu_communicator.query(SbuCommands.request_wakeup_reason)
        return WakeupReason(wakeup_reason_code)

    def set_wakeup_reason(self, reason: str) -> None:
        self._sbu_communicator.write(SbuCommands.set_wakeup_reason, payload=reason)

    def write_to_display(self, line1: str, line2: str) -> None:
        self.check_display_line_for_length(line1)
        self.check_display_line_for_length(line2)
        self._sbu_communicator.write(SbuCommands.write_to_display_line1, line1[:16])
        self._sbu_communicator.write(SbuCommands.write_to_display_line2, line2[:16])

    @staticmethod
    def check_display_line_for_length(line: str) -> None:
        if len(line) > 16:
            LOG.warning(f"Display string {line} is too long!")

    def set_display_brightness_percent(self, display_brightness_in_percent: float) -> None:
        self._sbu_communicator.write(
            SbuCommands.set_display_brightness, str(self._condition_brightness_value(display_brightness_in_percent))
        )

    def set_led_brightness_percent(self, led_brightness_in_percent: float) -> None:
        self._sbu_communicator.write(
            SbuCommands.set_led_brightness, str(self._condition_brightness_value(led_brightness_in_percent))
        )

    @staticmethod
    def _condition_brightness_value(brightness_in_percent: float) -> int:
        brightness_16bit = int(brightness_in_percent / 100 * 65535)
        maximum_brightness = 65535  # 16bit
        if brightness_16bit > maximum_brightness:
            LOG.warning(f"clipping brightness value from {brightness_16bit} to maximum ({maximum_brightness}).")
            brightness_16bit = maximum_brightness
        elif brightness_16bit < 0:
            LOG.warning(f"Brightness shall not be negative. Clipping to zero.")
            brightness_16bit = 0
        return brightness_16bit

    def send_seconds_to_next_bu(self, seconds: int) -> None:
        command = SbuCommands.set_seconds_to_next_bu
        payload = str(int(seconds))
        LOG.info(f"Command: message_code = {command.message_code}, payload = {payload}")
        assertion_message = self._sbu_communicator.query(command, payload)
        self._assert_correct_rtc_setting(assertion_message, seconds)

    @staticmethod
    def _assert_correct_rtc_setting(assertion_message: str, seconds: int) -> None:
        # Todo: Remove the following assertion and write proper tests for SBU code!
        value_in_cmp_register = int(findall(r"\d+", assertion_message)[0])
        seconds_in_cmp_register = int(seconds / 32)
        if not value_in_cmp_register == seconds_in_cmp_register:
            LOG.error(
                f"SBU didn't calculate the time to next backup correctly. "
                f"{seconds}/32={seconds_in_cmp_register} != {value_in_cmp_register}."
            )

    def send_readable_timestamp(self, timestamp: str) -> None:
        self._sbu_communicator.write(SbuCommands.send_readable_timestamp_of_next_bu, timestamp)

    def measure_base_input_current(self) -> Optional[float]:
        return self._measure(SbuCommands.measure_current)

    def measure_vcc3v_voltage(self) -> Optional[float]:
        return self._measure(SbuCommands.measure_vcc3v)

    def measure_sbu_temperature(self) -> Optional[float]:
        return self._measure(SbuCommands.measure_temperature)

    def _measure(self, command: SbuCommand) -> Optional[float]:
        response = self._sbu_communicator.query(command)
        response_16bit_value = self._extract_digits(response)
        return self._convert_measurement_result(command, response_16bit_value)

    @staticmethod
    def _extract_digits(response: str) -> int:
        return int(findall(r"[0-9]+", response[2:])[0])

    @staticmethod
    def _convert_measurement_result(command: SbuCommand, raw_value: int) -> Optional[float]:
        try:
            return _sbu_measurement_data_conversion_map[command.message_code](raw_value)
        except KeyError:
            LOG.warning(f"cannot convert anything from {command.message_code} (raw value given is {raw_value})")
            return None

    def request_shutdown(self) -> None:
        self._sbu_communicator.write(SbuCommands.request_shutdown)

    def abort_shutdown(self) -> None:
        self._sbu_communicator.write(SbuCommands.abort_shutdown)
