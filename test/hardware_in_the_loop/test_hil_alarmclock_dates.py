from datetime import datetime, timedelta
from time import sleep

import pytest

import base.hardware.pcu as pcu


@pytest.mark.hardware_in_the_loop
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "date_setter, date_getter",
    [
        (pcu.set.date.now, pcu.get.date.now),
        (pcu.set.date.backup, pcu.get.date.backup),
        (pcu.set.date.wakeup, pcu.get.date.wakeup),
    ]
)
async def test_set_get_date_now(date_setter, date_getter):
    nowish = datetime(2000, 1, 1, 0, 0)
    await date_setter(nowish)
    sleep(0.2)
    later = await date_getter()
    assert (later - nowish) < timedelta(seconds=3)
