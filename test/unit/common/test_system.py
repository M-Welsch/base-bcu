import logging
import subprocess
from subprocess import PIPE, Popen
from typing import Optional, Type

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from base.common.exceptions import NetworkError
from base.common.system import SmbShareMount, System


def test_size_of_next_backup_increment() -> None:
    ...


def test_copy_newest_backup_with_hardlinks() -> None:
    ...


@pytest.mark.parametrize(
    "str_in_stderr, exception, log_message",
    [
        ("everything_allright", None, "everything_allright"),
        ("error(16)", None, "Device probably already (un)mounted"),
        ("error(2)", NetworkError, ""),
        ("could not resolve address", NetworkError, ""),
    ],
)
def test_parse_process_output(
        str_in_stderr: str,
        exception: Optional[Type[Exception]],
        log_message: str,
        caplog: LogCaptureFixture,
) -> None:
    def function_under_test(process_for_test: Popen) -> None:
        SmbShareMount._parse_process_output(process_for_test)

    process = Popen(f'echo "{str_in_stderr}" 1>&2', shell=True, stderr=PIPE, stdout=PIPE)
    with caplog.at_level(logging.DEBUG):
        if exception is not None:
            with pytest.raises(exception):
                function_under_test(process)
        else:
            function_under_test(process)
        assert log_message in caplog.text


@pytest.mark.parametrize("timedatectl_output, result", [
    (b'               Local time: Di 2022-09-27 20:13:40 CEST\n           Universal time: Di 2022-09-27 18:13:40 UTC\n                 RTC time: Di 2022-09-27 18:13:40\n                Time zone: Europe/Berlin (CEST, +0200)\nSystem clock synchronized: yes\n              NTP service: active\n          RTC in local TZ: no\n', True),
    (b'               Local time: Di 2022-09-27 20:13:40 CEST\n           Universal time: Di 2022-09-27 18:13:40 UTC\n                 RTC time: Di 2022-09-27 18:13:40\n                Time zone: Europe/Berlin (CEST, +0200)\nSystem clock synchronized: no\n              NTP service: active\n          RTC in local TZ: no\n', False),
])
def test_system_clock_synchronized_with_ntp(timedatectl_output: bytes, result: bool, mocker: MockFixture) -> None:
    mocker.patch("subprocess.check_output", return_value=timedatectl_output)
    assert System.system_clock_synchronized_with_ntp() == result
