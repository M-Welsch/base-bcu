from dataclasses import dataclass


@dataclass
class SbuCommand:
    message_code: str
    response_keyword: str = ""


class SbuCommands:
    test = SbuCommand(message_code="Test", response_keyword="Echo")
    write_to_display_line1 = SbuCommand(message_code="D1")
    write_to_display_line2 = SbuCommand(message_code="D2")
    set_display_brightness = SbuCommand(message_code="DB")
    set_led_brightness = SbuCommand(message_code="DL")
    set_seconds_to_next_bu = SbuCommand(message_code="BU", response_keyword="CMP")
    get_seconds_to_next_bu = SbuCommand(message_code="BG")
    send_readable_timestamp_of_next_bu = SbuCommand(message_code="BR")
    read_readable_timestamp_of_next_bu = SbuCommand(message_code="BS")
    measure_current = SbuCommand(message_code="CC", response_keyword="CC")
    measure_vcc3v = SbuCommand(message_code="3V", response_keyword="3V")
    measure_temperature = SbuCommand(message_code="TP", response_keyword="TP")
    request_shutdown = SbuCommand(message_code="SR")
    abort_shutdown = SbuCommand(message_code="SA")
    request_wakeup_reason = SbuCommand(message_code="WR")
    set_wakeup_reason = SbuCommand(message_code="WD")
