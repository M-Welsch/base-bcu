import sys
from pathlib import Path
from platform import machine

from base.hardware.platform import platform_with_sbu


def pytest_configure() -> None:
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    from base.common.logger import LoggerFactory

    LoggerFactory(Path.cwd() / "base/log", "BaSe_test", development_mode=True)

    if not platform_with_sbu():
        from importlib import import_module

        sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")
        print("Not on SBC")
