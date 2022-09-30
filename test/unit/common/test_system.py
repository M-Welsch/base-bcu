import logging
from subprocess import PIPE, Popen
from typing import Optional, Type

import pytest
from _pytest.logging import LogCaptureFixture

from base.common.exceptions import NetworkError
from base.common.system import NetworkShareMount


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
        NetworkShareMount._parse_process_output(process_for_test)

    process = Popen(f'echo "{str_in_stderr}" 1>&2', shell=True, stderr=PIPE, stdout=PIPE)
    with caplog.at_level(logging.DEBUG):
        if exception is not None:
            with pytest.raises(exception):
                function_under_test(process)
        else:
            function_under_test(process)
        assert log_message in caplog.text
