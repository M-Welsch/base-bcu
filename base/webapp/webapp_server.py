import asyncio
from threading import Thread

import websockets
from signalslot import Signal

from base.common.config import Config
from base.common.exceptions import MountingError
from base.common.logger import LoggerFactory
from base.webapp.config_data import get_config_data, update_config_data


LOG = LoggerFactory.get_logger(__name__)


class WebappServer(Thread):
    webapp_event = Signal()
    reschedule_request = Signal()
    display_brightness_change = Signal(args=['brightness'])
    display_text = Signal(args=['text'])

    def __init__(self, codebook):
        super().__init__()
        self._codebook = codebook
        self._start_server = websockets.serve(self.echo, "0.0.0.0", 8453)
        self._event_loop = asyncio.get_event_loop()
        self.current_status = None

    def on_status(self, status, **kwargs):
        print(status)

    async def echo(self, websocket, path):
        try:
            message = await websocket.recv()
            print(f"< {message}")
            if message in self._codebook:
                self.webapp_event.emit(payload=message)

            if message == "heartbeat?" and self.current_status is not None:
                await websocket.send(self.current_status)
            elif message == "request_config":
                await websocket.send(get_config_data())
            elif message.startswith("new config: "):
                update_config_data(message[len("new config: "):])
                Config.config_changed.emit()
                self.reschedule_request.emit()
            elif message.startswith("display brightness: "):
                payload = message[len("display brightness: "):]
                try:
                    self.display_brightness_change.emit(brightness=float(payload))
                except ValueError:
                    LOG.warning(f"cannot process brightness value: {payload}")
            elif message.startswith("display text: "):
                payload = message[len("display text: "):]
                # Todo: äöü etc are displayed strangely
                self.display_text.emit(text=payload)
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
        except MountingError as e:
            LOG.error(f"Mounting error occurred: {e}")  # TODO: Display error message in webapp

    def run(self):
        self._event_loop.run_until_complete(self._start_server)
        self._event_loop.run_forever()
