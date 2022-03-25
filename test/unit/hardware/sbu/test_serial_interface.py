import sys
from importlib import import_module
from pathlib import Path
from time import time
from typing import Generator

import pytest
import serial
from pytest_mock import MockFixture

from base.common.config import Config
from base.common.exceptions import SbuCommunicationTimeout, SerialInterfaceError
from base.hardware.sbu.commands import SbuCommand
from base.hardware.sbu.message import SbuMessage

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.hardware.sbu.serial_interface import SerialInterface


@pytest.fixture()
def serial_interface() -> Generator["SerialInterface", None, None]:

    SerialInterface._config = Config(
        {"sbu_response_timeout": 0.001, "wait_for_channel_free_timeout": 0.001, "serial_connection_timeout": 1}
    )
    yield SerialInterface(port=Path(), baud_rate=5678)


def test_setup_teardown(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.open")
    patched_set_sbu_serial_path_to_communication = mocker.patch(
        "base.hardware.pin_interface.PinInterface.set_sbu_serial_path_to_communication"
    )
    patched_enable_receiving_messages_from_sbu = mocker.patch(
        "base.hardware.pin_interface.PinInterface.enable_receiving_messages_from_sbu"
    )
    patched_disable_receiving_messages_from_sbu = mocker.patch(
        "base.hardware.pin_interface.PinInterface.disable_receiving_messages_from_sbu"
    )
    patched_wait_for_channel_free = mocker.patch(
        "base.hardware.sbu.serial_interface.SerialInterface._wait_for_channel_free"
    )
    patched_flush_sbu_channel = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    with serial_interface as interface:
        assert isinstance(interface._serial_connection, serial.Serial)
        assert patched_wait_for_channel_free.called_once_with()
        assert patched_set_sbu_serial_path_to_communication.called_once_with()
        assert patched_enable_receiving_messages_from_sbu.called_once_with()
        assert patched_flush_sbu_channel.called_once_with()
    assert patched_disable_receiving_messages_from_sbu.called_once_with()
    assert patched_flush_sbu_channel.call_count == 2


def test_connect_serial_communication_path(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.open")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    patched_set_sbu_serial_path_to_communication = mocker.patch(
        "base.hardware.pin_interface.PinInterface.set_sbu_serial_path_to_communication"
    )
    patched_enable_receiving_messages_from_sbu = mocker.patch(
        "base.hardware.pin_interface.PinInterface.enable_receiving_messages_from_sbu"
    )
    with serial_interface as interface:
        patched_set_sbu_serial_path_to_communication.reset_mock()
        patched_enable_receiving_messages_from_sbu.reset_mock()
        start = time()
        interface._connect_serial_communication_path()
        duration = time() - start
    assert patched_set_sbu_serial_path_to_communication.called_once_with()
    assert patched_enable_receiving_messages_from_sbu.called_once_with()
    assert duration > 4e-8


def test_establish_serial_connection_or_raise(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    with pytest.raises(SerialInterfaceError):
        with serial_interface as interface:
            interface._port = Path("None!")
            interface._establish_serial_connection_or_raise()


def test_close_connection(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._wait_for_channel_free")
    mocker.patch("serial.Serial.open")
    patched_close = mocker.patch("serial.Serial.close")
    with serial_interface as interface:
        patched_close.reset_mock()
        interface._close_connection()
        assert patched_close.called_once_with()


def test_close_connection_no_error(serial_interface: SerialInterface) -> None:
    serial_interface._close_connection()


def test_reset_buffers(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._wait_for_channel_free")
    mocker.patch("serial.Serial.open")
    patched_reset_input_buffer = mocker.patch("serial.Serial.reset_input_buffer")
    patched_reset_output_buffer = mocker.patch("serial.Serial.reset_output_buffer")
    with serial_interface as interface:
        patched_reset_input_buffer.reset_mock()
        patched_reset_output_buffer.reset_mock()
        interface.reset_buffers()
        assert patched_reset_input_buffer.called_once_with()
        assert patched_reset_output_buffer.called_once_with()


def test_reset_buffers_error(serial_interface: SerialInterface) -> None:
    with pytest.raises(RuntimeError):
        serial_interface.reset_buffers()


def test_flush_sbu_channel(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.open")
    patched_send_message = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._send_message")
    with serial_interface as interface:
        patched_send_message.reset_mock()
        interface.flush_sbu_channel()
        assert patched_send_message.called_once_with(b"\0")


def test_write_to_sbu(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.open")
    patched_send_message = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._send_message")
    patched_await_acknowledge = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._await_acknowledge")
    patched_wait_for_sbu_ready = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._wait_for_sbu_ready")
    message = SbuMessage(command=SbuCommand(message_code="CODE"), payload="Message in a bottle?")
    with serial_interface as interface:
        patched_send_message.reset_mock()
        interface.write_to_sbu(message=message)
        assert patched_send_message.called_once_with(message=message.binary)
        assert patched_await_acknowledge.called_once_with(message.code)
        assert patched_wait_for_sbu_ready.called_once_with()


def test_query_from_sbu(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    expected = "response"
    mocker.patch("serial.Serial.open")
    patched_send_message = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._send_message")
    patched_await_acknowledge = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._await_acknowledge")
    patched_wait_for_response = mocker.patch(
        "base.hardware.sbu.serial_interface.SerialInterface._wait_for_response", return_value=(0, expected)
    )
    patched_wait_for_sbu_ready = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._wait_for_sbu_ready")
    message = SbuMessage(
        command=SbuCommand(message_code="CODE", response_keyword="RKW"),
        payload="Message in a bottle?",
    )
    with serial_interface as interface:
        patched_send_message.reset_mock()
        response = interface.query_from_sbu(message=message)
        assert patched_send_message.called_once_with(message=message.binary)
        assert patched_await_acknowledge.called_once_with(message.code)
        assert patched_wait_for_response.called_once_with(message.response_keyword)
        assert patched_wait_for_sbu_ready.called_once_with()
        assert response == expected


def test_query_from_sbu__no_response_keyword(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    expected = "response"
    mocker.patch("serial.Serial.open")
    patched_send_message = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._send_message")
    patched_await_acknowledge = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._await_acknowledge")
    patched_wait_for_response = mocker.patch(
        "base.hardware.sbu.serial_interface.SerialInterface._wait_for_response", return_value=(0, expected)
    )
    patched_wait_for_sbu_ready = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._wait_for_sbu_ready")
    message = SbuMessage(
        command=SbuCommand(message_code="CODE", response_keyword=""),
        payload="Message in a bottle?",
    )
    with serial_interface as interface:
        patched_send_message.reset_mock()
        response = interface.query_from_sbu(message=message)
        assert patched_send_message.called_once_with(message=message.binary)
        assert patched_await_acknowledge.called_once_with(message.code)
        assert patched_wait_for_response.called_once_with(message.response_keyword)
        assert patched_wait_for_sbu_ready.called_once_with()
        assert response == expected


def test_send_message(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.open")
    mocker.patch("serial.Serial.write")
    message = b"Dream Theater rocks!"
    with serial_interface as interface:
        # noinspection PyUnresolvedReferences
        serial.Serial.write.reset_mock()
        interface._send_message(message)
        # noinspection PyUnresolvedReferences
        assert serial.Serial.write.called_once_with(message)


def test_send_message_error(serial_interface: SerialInterface) -> None:
    with pytest.raises(RuntimeError):
        serial_interface._send_message(b"I'm going nowhere! :-(")


def test_wait_for_channel_free__n_busy_n_ready(serial_interface: SerialInterface) -> None:
    SerialInterface._channel_busy = False
    SerialInterface._sbu_ready = False
    with pytest.raises(SbuCommunicationTimeout):
        serial_interface._wait_for_channel_free()


def test_wait_for_channel_free__n_busy_ready(serial_interface: SerialInterface) -> None:
    SerialInterface._channel_busy = False
    SerialInterface._sbu_ready = True
    serial_interface._wait_for_channel_free()


def test_wait_for_channel_free__busy_n_ready(serial_interface: SerialInterface) -> None:
    SerialInterface._channel_busy = True
    SerialInterface._sbu_ready = False
    with pytest.raises(SbuCommunicationTimeout):
        serial_interface._wait_for_channel_free()


def test_wait_for_channel_free__busy_ready(serial_interface: SerialInterface) -> None:
    SerialInterface._channel_busy = True
    SerialInterface._sbu_ready = True
    with pytest.raises(SbuCommunicationTimeout):
        serial_interface._wait_for_channel_free()


def test_wait_for_response_timeout(serial_interface: SerialInterface) -> None:
    with pytest.raises(SbuCommunicationTimeout):
        with serial_interface as interface:
            interface._wait_for_response("")


def test_wait_for_response(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.open")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    response = "response"
    mocker.patch("serial.Serial.read_until", return_value=response.encode())
    SerialInterface._channel_busy = False
    SerialInterface._sbu_ready = True
    serial.Serial.response = response
    with serial_interface as interface:
        interface._wait_for_response(response)


def test_await_acknowledge(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.open")
    patched_wait_for_response = mocker.patch(
        "base.hardware.sbu.serial_interface.SerialInterface._wait_for_response", return_value=(0, "response")
    )
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    message_code = "message_code"
    with serial_interface as interface:
        interface._await_acknowledge(message_code)
        assert patched_wait_for_response.called_once_with(f"ACK:{message_code}")


def test_wait_for_sbu_ready(serial_interface: SerialInterface, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.open")
    patched_wait_for_response = mocker.patch(
        "base.hardware.sbu.serial_interface.SerialInterface._wait_for_response", return_value=(0, "response")
    )
    patched_flush_sbu_channel = mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    with serial_interface as interface:
        patched_flush_sbu_channel.reset_mock()
        interface._wait_for_sbu_ready()
        assert patched_wait_for_response.called_once_with("Ready")
        assert patched_flush_sbu_channel.called_once_with()
