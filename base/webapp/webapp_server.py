import asyncio
import logging
from pathlib import Path
from threading import Thread

import websockets
from signalslot import Signal

LOG = logging.getLogger(Path(__file__).name)


class WebappServer(Thread):

    webapp_event = Signal()

    def __init__(self, codebook):
        super().__init__()
        self._codebook = codebook
        self._start_server = websockets.serve(self.echo, "0.0.0.0", 8453)
        self._event_loop = asyncio.get_event_loop()

    def on_status(self, status, **kwargs):
        print(status)

    async def echo(self, websocket, path):
        try:
            message = await websocket.recv()
            print(f"< {message}")
            if message in self._codebook:
                self.webapp_event.emit(payload=message)

            # greeting = f"Hello {message}!"
            #
            # await websocket.send(greeting)
            # print(f"> {greeting}")
        except websockets.exceptions.ConnectionClosedOK as e:
            LOG.debug(f"Client went away: {e}")

    def run(self):
        self._event_loop.run_until_complete(self._start_server)
        self._event_loop.run_forever()
