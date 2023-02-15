import asyncio
import logging

from base.asyncio_demo.backup_conductor import BackupConductor
from base.asyncio_demo.base_application import BaseApplication
from base.asyncio_demo.heartbeat import Heartbeat
from base.asyncio_demo.shutdown_manager import ShutdownManager
from base.asyncio_demo.standby_unit import StandbyUnit


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(module)s %(message)s"
)


async def main():
    shutdown_manager = ShutdownManager(seconds=5)
    standby_unit = StandbyUnit()
    backup_conductor = BackupConductor()
    app = BaseApplication(
        shutdown_manager=shutdown_manager, standby_unit=standby_unit, backup_conductor=backup_conductor
    )
    with Heartbeat():
        await app.run()


if __name__ == "__main__":
    asyncio.run(main())
