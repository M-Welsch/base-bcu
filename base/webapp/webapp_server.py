import asyncio
import json
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set, Tuple

import websockets
from signalslot import Signal

from base.common.config import BoundConfig
from base.common.exceptions import BackupHddNotAvailable, DockingError, MountError
from base.common.logger import LoggerFactory
from base.hardware.hardware import Hardware
from base.logic.backup.backup_browser import BackupBrowser
from base.webapp.config_data import get_config_data, update_config_data
from base.webapp.log_data import list_logfiles, logfile_content

LOG = LoggerFactory.get_logger(__name__)


class WebappServer:
    backup_now_request = Signal()
    backup_abort = Signal()
    reschedule_request = Signal()

    def __init__(self, hardware: Hardware) -> None:
        self.current_status: Optional[str] = None
        self._hardware = hardware
        self._codebook: Dict[str, Callable] = {
            "heartbeat": self._heartbeat,
            "dock": self._dock,
            "undock": self._undock,
            "power": self._power,
            "unpower": self._unpower,
            "mount": self._mount,
            "unmount": self._unmount,
            "backup_now": self._backup_now,
            "backup_abort": self._backup_abort,
            "request_config": self._request_config,
            "new_config": self._new_config,
            "display_brightness": self._display_brightness,
            "display_text": self._display_text,
            "backup_index": self._backup_index,
            "logfile_index": self._logfile_index,
            "request_logfile": self._request_logfile,
        }

    def start(self) -> None:
        LOG.info("Starting webserver")
        start_server = websockets.serve(self.handler, "0.0.0.0", 8453)
        asyncio.get_event_loop().run_until_complete(start_server)
        LOG.info("Webserver started")

    async def handler(self, websocket: websockets.WebSocketServer, path: Path) -> None:
        try:
            raw_message: str = await websocket.recv()
            print(f"< {raw_message}")
            message_code, payload = self._decode_message(raw_message)
            response = self._codebook[message_code](payload)
            if response is not None:
                await websocket.send(response)
        except KeyError:
            LOG.error(f"got invalid message_code: {raw_message}")
        except json.decoder.JSONDecodeError as e:
            LOG.debug(f"cannot decode: {e}")
        except websockets.exceptions.ConnectionClosedOK as e:
            LOG.debug(f"Client went away: {e}")
        except websockets.exceptions.ConnectionClosedError as e:
            LOG.debug(f"Connection died X-P : {e}")
        except websockets.exceptions.ConnectionClosed as e:
            LOG.debug(f"Connection died :-( : {e}")

    @staticmethod
    def _decode_message(raw_message: str) -> Tuple[str, Any]:
        package = json.loads(raw_message)
        return package["code"], package.get("payload", None)

    def _heartbeat(self, payload: str) -> str:
        return self.current_status if self.current_status is not None else ""

    def _dock(self, payload: str) -> Optional[str]:
        try:
            self._hardware.dock()
        except DockingError:
            pass
        return None

    def _undock(self, payload: str) -> Optional[str]:
        try:
            self._hardware.undock()
        except DockingError:
            pass
        return None

    def _power(self, payload: str) -> Optional[str]:
        self._hardware.power()
        return None

    def _unpower(self, payload: str) -> Optional[str]:
        self._hardware.unpower()
        return None

    def _mount(self, payload: str) -> Optional[str]:
        try:
            self._hardware.mount()
        except BackupHddNotAvailable:
            pass
        except MountError:
            pass
        return None

    def _unmount(self, payload: str) -> Optional[str]:
        self._hardware.unmount()
        return None

    def _backup_now(self, _: str) -> str:
        LOG.info("Backup requested by user via webapp")
        self.backup_now_request.emit()
        return "backup_request_acknowledged"

    def _backup_abort(self, _: str) -> str:
        LOG.info("Backup abort requested by user via webapp")
        self.backup_abort.emit()
        return "backup_abort_acknowledged"

    def _request_config(self, _: str) -> str:
        return get_config_data()

    def _new_config(self, payload: dict) -> None:
        update_config_data(payload)
        BoundConfig.reload_all()
        self.reschedule_request.emit()

    def _display_brightness(self, payload: float) -> None:
        try:
            self._hardware.set_display_brightness(payload)
        except ValueError:
            LOG.warning(f"cannot process brightness value: {payload}")

    def _display_text(self, payload: dict) -> None:
        line1 = payload.get("line1", "")
        line2 = payload.get("line2", "")
        self._hardware.write_to_display(line1, line2)

    def _backup_index(self, payload: str) -> str:
        return json.dumps(BackupBrowser().index)

    def _logfile_index(self, payload: str) -> str:
        return json.dumps(list_logfiles(newest_first=True))

    def _request_logfile(self, payload: str) -> str:
        return json.dumps(logfile_content(payload, recent_line_first=True))
