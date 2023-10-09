from typing import Iterable

from base.asyncio_demo.backup_conductor import BackupConductor
from base.asyncio_demo.logger import get_logger
from base.asyncio_demo.shutdown_manager import ShutdownManager
from base.asyncio_demo.standby_unit import StandbyUnit
from base.asyncio_demo.state import State
from base.asyncio_demo.ui import UI
from base.asyncio_demo.util import calculate_backup_time

log = get_logger(__name__)


class BaseApplication:
    def __init__(
        self,
        # state: State,
        shutdown_manager: ShutdownManager,
        standby_unit: StandbyUnit,
        backup_conductor: BackupConductor,
        user_interfaces: Iterable[UI],
    ):
        log.debug("Initializing...")
        # self._state = state
        self._shutdown_manager = shutdown_manager
        self._standby_unit = standby_unit
        self._backup_conductor = backup_conductor
        self._user_interfaces = user_interfaces
        self._connect_signals()

    def _connect_signals(self):
        async def print_bytes(line: bytes) -> None:
            print(line)

        self._backup_conductor.backup_started.connect(self._shutdown_manager.pause)
        self._backup_conductor.backup_finished.connect(self._shutdown_manager.reset)
        self._backup_conductor.line_written.connect(print_bytes)
        self._backup_conductor.critical.connect(self._shutdown_manager.reset)

        for interface in self._user_interfaces:
            self._shutdown_manager.seconds_changed.connect(interface.on_shutdown_seconds_changed)
            interface.signals.shutdown_countdown_paused.connect(self._shutdown_manager.pause)
            interface.signals.shutdown_countdown_reset.connect(self._shutdown_manager.reset)

    async def run(self):
        log.debug("I am awake. But why?")
        wakeup_reason = await self._standby_unit.get_wakeup_reason()
        log.debug(f"Ah, because {wakeup_reason}")

        self._shutdown_manager.start()
        self._backup_conductor.set(backup_time=calculate_backup_time(wakeup_reason=wakeup_reason))
        await self._shutdown_manager
