import asyncio

from base.common.logger import LoggerFactory
from base.hardware.drivers.pin_interface import pin_interface

LOG = LoggerFactory.get_logger(__name__)


class Buttons:
    _button_poll_interval = 0.2

    def __init__(self):
        self._task = asyncio.create_task(self._poll_button_states())

    async def _poll_button_states(self):
        previous_0, previous_1 = 0, 0
        while True:
            button_0_state = pin_interface.button_0_pin_high
            if button_0_state and not previous_0:
                LOG.debug("Button 0 was pressed!")
            button_1_state = pin_interface.button_1_pin_high
            if button_1_state and not previous_1:
                LOG.debug("Button 1 was pressed!")
            previous_0, previous_1 = button_0_state, button_1_state
            await asyncio.sleep(self._button_poll_interval)
