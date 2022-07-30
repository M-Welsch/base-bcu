from typing import Generator

import pytest

from base.hardware.hmi import Hmi, HmiStates
from base.hardware.sbu.communicator import SbuCommunicator
from base.hardware.sbu.sbu import SBU
from base.logic.schedule import Schedule


@pytest.fixture
def hmi() -> Generator[Hmi, None, None]:
    # configs not patched yet. Not important yet.
    sbu_communicator = SbuCommunicator()
    sbu = SBU(sbu_communicator=sbu_communicator)
    schedule = Schedule()
    yield Hmi(sbu, schedule)


def test_display_waiting_for_backup(hmi: Hmi) -> None:
    line1, line2 = hmi._display_waiting_for_backup()
    assert len(line1) == 16
    assert len(line2) == 16


@pytest.mark.parametrize("hmi_state", [HmiStates.starting_up, HmiStates.waiting_for_backup, HmiStates.backup_running, HmiStates.waiting_for_shutdown])
def test_hmi_print_status(hmi: Hmi, hmi_state: HmiStates) -> None:
    hmi._schedule.on_reschedule_backup()
    hmi._state = hmi_state
    if hmi_state == HmiStates.waiting_for_backup:
        hmi.display_status()
