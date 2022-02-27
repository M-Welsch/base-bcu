import asyncio
import json
from pathlib import Path
from threading import Thread
from typing import Optional, Set

import websockets
from signalslot import Signal

from base.common.config import BoundConfig
from base.common.exceptions import MountError
from base.common.logger import LoggerFactory
from base.logic.backup.backup_browser import BackupBrowser
from base.webapp.config_data import get_config_data, update_config_data
from base.webapp.log_data import list_logfiles, logfile_content

LOG = LoggerFactory.get_logger(__name__)


class WebappServer(Thread):
    webapp_event = Signal()
    backup_now_request = Signal()
    backup_abort = Signal()
    reschedule_request = Signal()
    display_brightness_change = Signal(args=["brightness"])
    display_text = Signal(args=["text"])

    def __init__(self, codebook: Set[str]) -> None:
        super().__init__()
        self._codebook = codebook
        self._start_server = websockets.serve(self.echo, "0.0.0.0", 8453)
        self._event_loop = asyncio.get_event_loop()
        self.current_status: Optional[str] = None

    async def echo(self, websocket: websockets.WebSocketServer, path: Path) -> None:
        try:
            message = await websocket.recv()
            print(f"< {message}")
            if message in self._codebook:
                self.webapp_event.emit(payload=message)
            elif message == "heartbeat?":
                if self.current_status is not None:
                    await websocket.send(self.current_status)
            elif message == "backup_now":
                LOG.info("Backup requested by user")
                # Todo: log some information about the requester
                self.backup_now_request.emit()
                await websocket.send("backup_request_acknowledged")
            elif message == "backup_abort":
                LOG.info("Backup abort requested by user")
                self.backup_abort.emit()
                await websocket.send("backup_abort_acknowledged")
            elif message == "request_config":
                await websocket.send(get_config_data())
            elif message.startswith("new config: "):
                update_config_data(message[len("new config: ") :])
                BoundConfig.reload_all()
                self.reschedule_request.emit()
            elif message.startswith("display brightness: "):
                payload = message[len("display brightness: ") :]
                try:
                    self.display_brightness_change.emit(brightness=float(payload))
                except ValueError:
                    LOG.warning(f"cannot process brightness value: {payload}")
            elif message.startswith("display text: "):
                payload = message[len("display text: ") :]
                # Todo: äöü etc are displayed strangely
                self.display_text.emit(text=payload)
            elif message.startswith("backup_index"):
                await websocket.send(json.dumps(BackupBrowser().index))
            elif message.startswith("logfile_index"):
                await websocket.send(json.dumps(list_logfiles(newest_first=True)))
            elif message.startswith("request_logfile"):
                logfile_name = message[len("request_logfile: ") :]
                await websocket.send(json.dumps(logfile_content(logfile_name, recent_line_first=True)))
            else:
                LOG.info(f"unknown message code: {message}")

            # greeting = f"Hello {message}!"
            #
            # await websocket.send(greeting)
            # print(f"> {greeting}")
        except websockets.exceptions.ConnectionClosedOK as e:
            LOG.debug(f"Client went away: {e}")
        except websockets.exceptions.ConnectionClosedError as e:
            LOG.debug(f"Connection died X-P : {e}")
        except websockets.exceptions.ConnectionClosed as e:
            LOG.debug(f"Connection died :-( : {e}")
        except MountError as e:
            LOG.error(f"Mounting error occurred: {e}")  # TODO: Display error message in webapp

    def run(self) -> None:
        self._event_loop.run_until_complete(self._start_server)
        self._event_loop.run_forever()
