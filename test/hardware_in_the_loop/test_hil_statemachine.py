from datetime import datetime, timedelta

import pytest
import base.hardware.pcu as pcu


@pytest.mark.hardware_in_the_loop
@pytest.mark.asyncio
async def test_hil_shutdown_init():
    init_outputs = await pcu.cmd.shutdown.init()
    deep_sleep_outputs = await pcu.check_messages(6)
    wakeup_outputs = await pcu.debugcmd.wakeup()
    wakeup_reason = await pcu.get.wakeup_reason()
    assert 'shutdown_requested state' in init_outputs
    assert 'deep_sleep state' in deep_sleep_outputs
    assert 'active state' in wakeup_outputs
    assert wakeup_reason == pcu.WakeupReason.WAKEUP_REASON_USER_REQUEST


@pytest.mark.hardware_in_the_loop
@pytest.mark.asyncio
async def test_hil_shutdown_init_and_abort():
    init_outputs = await pcu.cmd.shutdown.init()
    abort_outputs = await pcu.cmd.shutdown.abort()
    assert 'shutdown_requested state' in init_outputs
    assert 'active state' in abort_outputs


@pytest.mark.hardware_in_the_loopk
@pytest.mark.asyncio
async def test_hil_shutdown_init_with_scheduled_wakeup():
    now = datetime.now()
    later = datetime.now() + timedelta(minutes=1)
    await pcu._set_date(pcu.DateKind.now, now)
    await pcu._set_date(pcu.DateKind.wakeup, later)
    init_outputs = await pcu.cmd.shutdown.init()
    deep_sleep_outputs = await pcu.check_messages(6)
    assert 'shutdown_requested state' in init_outputs
    assert 'deep_sleep state' in deep_sleep_outputs

    wakeup_outputs = await pcu.check_messages(120)
    assert 'active state' in wakeup_outputs
    wakeup_reason = await pcu.get.wakeup_reason()
    assert wakeup_reason == pcu.WakeupReason.WAKEUP_REASON_SCHEDULED


@pytest.mark.hardware_in_the_loop
@pytest.mark.asyncio
async def test_hil_shutdown_with_wakeup_into_hmi():
    init_outputs = await pcu.cmd.shutdown.init()
    assert 'shutdown_requested state' in init_outputs

    deep_sleep_outputs = await pcu.check_messages(6)
    assert 'deep_sleep state' in deep_sleep_outputs

    button_pressed_outputs = await pcu.debugcmd.button_pressed(0)
    assert 'hmi state' in button_pressed_outputs

    wakeup_outputs = await pcu.debugcmd.wakeup()
    assert 'active state' in wakeup_outputs

    wakeup_reason = await pcu.get.wakeup_reason()
    assert wakeup_reason == pcu.WakeupReason.WAKEUP_REASON_USER_REQUEST
