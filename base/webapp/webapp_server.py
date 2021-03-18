import asyncio
from threading import Thread

import websockets
from signalslot import Signal


class WebappServer(Thread):
    backup_now = Signal()

    def __init__(self):
        super().__init__()
        self._start_server = websockets.serve(self.echo, "0.0.0.0", 8453)
        self._event_loop = asyncio.get_event_loop()

    def on_status(self, status, **kwargs):
        print(status)

    @staticmethod
    async def echo(websocket):
        name = await websocket.recv()
        print(f"< {name}")

        greeting = f"Hello {name}!"

        await websocket.send(greeting)
        print(f"> {greeting}")

    def run(self):
        self._event_loop.run_until_complete(self._start_server)
        self._event_loop.run_forever()
