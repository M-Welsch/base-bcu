import asyncio
import logging
from typing import Iterable

from base.asyncio_demo.backup_conductor import BackupConductor
from base.asyncio_demo.base_application import BaseApplication
from base.asyncio_demo.heartbeat import Heartbeat
from base.asyncio_demo.logger import setup_logger
from base.asyncio_demo.network.server import WebappServer
from base.asyncio_demo.shutdown_manager import ShutdownManager
from base.asyncio_demo.standby_unit import StandbyUnit
from base.asyncio_demo.state import BackupDriveState, DiagnoseData, SerialInterface, State
from base.asyncio_demo.ui import UI
from base.asyncio_demo.ui.hardware_ui import HardwareUI
from base.asyncio_demo.ui.web_ui import WebUI


async def main():
    setup_logger(debug=True)

    # observers = [HardwareUI(SerialInterface(), {"voltage", "current"})]
    # dd = DiagnoseData(observers=observers)
    # bds = BackupDriveState(observers=observers, is_docked=True, is_powered=True, is_mounted=False)
    # # wsm = WebSocketModul(observers=[])
    # state = State(diagnose_data=dd, backup_drive_state=bds)
    #
    # # wsm.set_state(state=state)

    shutdown_manager = ShutdownManager(seconds=5)
    standby_unit = StandbyUnit()
    backup_conductor = BackupConductor()
    webapp_server = WebappServer()
    user_interfaces: Iterable[UI] = [HardwareUI(), WebUI(webapp_server)]
    # user_interfaces: Iterable[UI] = [HardwareUI(state=state), WebUI(state=state)]

    app = BaseApplication(
        # state=state,
        shutdown_manager=shutdown_manager,
        standby_unit=standby_unit,
        backup_conductor=backup_conductor,
        user_interfaces=user_interfaces,
    )
    with Heartbeat():
        with webapp_server:
            await app.run()


if __name__ == "__main__":
    asyncio.run(main())
