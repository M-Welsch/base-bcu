from base.asyncio_demo.logger import get_logger
from base.asyncio_demo.network.server import WebappServer
from base.asyncio_demo.ui import UI

log = get_logger(__name__)


class WebUI(UI):
    def __init__(self, webapp_server: WebappServer):
        super().__init__()
        self._webapp_server = webapp_server
        self._webapp_server.set_interface(
            {
                "pause_shutdown_timer": self.signals.shutdown_countdown_paused,
                "resume_shutdown_timer": self.signals.shutdown_countdown_reset,
            }
        )

    async def on_shutdown_seconds_changed(self, remaining_seconds: float):
        log.debug(f"Sending {remaining_seconds=} until shutdown to web ui...")
        # TODO: Das funktioniert irgendwie nicht:
        await self._webapp_server.send({"topic": "shutdown_timer_state", "data": {"seconds": round(remaining_seconds)}})

    def on_diagnose_data(self, diagnose_data) -> None:
        log.debug(f"Sending {diagnose_data=} to web ui...")

    def on_backup_started(self) -> None:
        log.debug(f"Notify web ui that a backup has started...")

    def on_backup_finished(self) -> None:
        log.debug(f"Notify web ui that a backup has finished...")

    def on_backup_progress_changed(self, percentage: float, current_file_name: str):
        log.debug(f"Sending backup_progress ({percentage * 100} %, {current_file_name=}) to web ui...")
