from dataclasses import dataclass


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
        message_code="D1", await_acknowledge=True, await_ready_signal=False  # yes, that's how it is!
    )
    write_to_display_line2 = SbuCommand(message_code="D2", await_acknowledge=True, await_ready_signal=True)
    set_display_brightness = SbuCommand(message_code="DB", await_acknowledge=True, await_ready_signal=True)
    set_led_brightness = SbuCommand(message_code="DL", await_acknowledge=True, await_ready_signal=True)
    set_seconds_to_next_bu = SbuCommand(
        message_code="BU", await_acknowledge=True, await_ready_signal=True, await_response=True, response_keyword="CMP"
    )
    send_readable_timestamp_of_next_bu = SbuCommand(
        message_code="BR", await_acknowledge=False, await_ready_signal=True  # Fixme: SBU Bug!
    )
    measure_current = SbuCommand(
        message_code="CC", await_acknowledge=True, await_ready_signal=True, await_response=True, response_keyword="CC"
    )
    measure_vcc3v = SbuCommand(
        message_code="3V", await_acknowledge=True, await_ready_signal=True, await_response=True, response_keyword="3V"
    )
    measure_temperature = SbuCommand(
        message_code="TP", await_acknowledge=True, await_ready_signal=True, await_response=True, response_keyword="TP"
    )
    request_shutdown = SbuCommand(message_code="SR", await_acknowledge=True, await_ready_signal=False)
    abort_shutdown = SbuCommand(message_code="SA", await_acknowledge=True, await_ready_signal=False)
    request_wakeup_reason = SbuCommand(
        message_code="WR", await_acknowledge=True, await_ready_signal=True, await_response=True
    )
    set_wakeup_reason = SbuCommand(
        message_code="WD", await_acknowledge=True, await_ready_signal=True, await_response=False
    )
