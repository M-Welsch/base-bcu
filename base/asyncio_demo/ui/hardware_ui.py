from base.asyncio_demo.logger import get_logger
from base.asyncio_demo.ui import UI

log = get_logger(__name__)


class HardwareUI(UI):
    async def on_shutdown_seconds_changed(self, remaining_seconds: float):
        log.debug(f"Sending {remaining_seconds=} until shutdown to hardware ui...")

    def on_diagnose_data(self, diagnose_data) -> None:
        log.debug(f"Sending {diagnose_data=} to hardware ui...")

    def on_backup_started(self) -> None:
        log.debug(f"Notify hardware ui that a backup has started...")

    def on_backup_finished(self) -> None:
        log.debug(f"Notify hardware ui that a backup has finished...")

    def on_backup_progress_changed(self, percentage: float, current_file_name: str):
        log.debug(f"Sending backup_progress ({percentage * 100} %, {current_file_name=}) to hardware ui...")
