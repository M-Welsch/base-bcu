import logging

from base.asyncio_demo.backup_conductor import BackupConductor
from base.asyncio_demo.shutdown_manager import ShutdownManager
from base.asyncio_demo.standby_unit import StandbyUnit
from base.asyncio_demo.util import calculate_backup_time


class BaseApplication:
    def __init__(self, shutdown_manager: ShutdownManager, standby_unit: StandbyUnit, backup_conductor: BackupConductor):
        logging.debug("Initializing...")
        self._shutdown_manager = shutdown_manager
        self._standby_unit = standby_unit
        self._backup_conductor = backup_conductor
        self._connect_signals()

    def _connect_signals(self):
        def print_bytes(line: bytes) -> None:
            print(line)

        self._backup_conductor.backup_started.connect(self._shutdown_manager.pause)
        self._backup_conductor.backup_finished.connect(self._shutdown_manager.reset)
        self._backup_conductor.line_written.connect(print_bytes)
        self._backup_conductor.critical.connect(self._shutdown_manager.reset)

    async def run(self):
        logging.debug("I am awake. But why?")
        wakeup_reason = await self._standby_unit.get_wakeup_reason()
        logging.debug(f"Ah, because {wakeup_reason}")

        self._shutdown_manager.start()
        self._backup_conductor.set(backup_time=calculate_backup_time(wakeup_reason=wakeup_reason))
        await self._shutdown_manager
