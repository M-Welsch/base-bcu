from typing import Generator

import pytest

from base.hardware.hardware import Hardware


@pytest.fixture
def hardware() -> Generator[Hardware, None, None]:
    hardware = Hardware()
    hardware.disengage()
    yield hardware


def test_engage(hardware: Hardware) -> None:
    hardware.engage()
