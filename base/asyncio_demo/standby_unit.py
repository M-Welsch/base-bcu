import asyncio

from base.asyncio_demo.wakeup_reason import WakeupReason


class StandbyUnit:
    async def get_wakeup_reason(self):
        await asyncio.sleep(0.5)
        return WakeupReason("SCHEDULED")
