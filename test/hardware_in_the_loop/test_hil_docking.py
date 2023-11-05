from time import sleep

import pytest

import base.hardware.pcu as pcu


@pytest.mark.hardware_in_the_loop
@pytest.mark.asyncio
async def test_dock():
    """ abbreviating dockingstate as ps """
    await pcu.cmd.power.fiveV.off()
    await pcu.cmd.power.hdd.off()
    ds_right_before_docking = await pcu.get.dockingstate()
    assert ds_right_before_docking == pcu.DockingState.pcu_dockingState1_undocked, "check if undocked, run again"
    await pcu.cmd.dock()
    sleep(2)
    ds_after_docking_has_happened = await pcu.get.dockingstate()
    assert ds_after_docking_has_happened == pcu.DockingState.pcu_dockingState2_allDockedPwrOff

    await pcu.cmd.power.hdd.on()
    ds_after_power_hdd = await pcu.get.dockingstate()
    assert ds_after_power_hdd == pcu.DockingState.pcu_dockingState4_allDocked12vOn

    await pcu.cmd.power.fiveV.on()
    ds_after_power_5v = await pcu.get.dockingstate()
    assert ds_after_power_5v == pcu.DockingState.pcu_dockingState3_allDockedPwrOn


@pytest.mark.hardware_in_the_loop
@pytest.mark.asyncio
async def test_undock():
    """ abbreviating dockingstate as ps """
    await pcu.cmd.power.fiveV.on()
    await pcu.cmd.power.hdd.on()

    ds_right_before_undocking = await pcu.get.dockingstate()
    assert ds_right_before_undocking == pcu.DockingState.pcu_dockingState3_allDockedPwrOn, "check if docked, run again"

    await pcu.cmd.power.fiveV.off()
    sleep(0.5)
    ds_after_unpower_5v = await pcu.get.dockingstate()
    assert ds_after_unpower_5v == pcu.DockingState.pcu_dockingState4_allDocked12vOn

    await pcu.cmd.power.hdd.off()
    ds_after_unpower_hdd = await pcu.get.dockingstate()
    assert ds_after_unpower_hdd == pcu.DockingState.pcu_dockingState2_allDockedPwrOff

    await pcu.cmd.undock()
    sleep(2)
    ds_after_undocking = await pcu.get.dockingstate()
    assert ds_after_undocking == pcu.DockingState.pcu_dockingState1_undocked
