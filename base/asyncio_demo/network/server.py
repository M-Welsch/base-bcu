import asyncio
import json
from asyncio import Future, Task
from typing import Dict, Optional, Set

from websockets import WebSocketServerProtocol, serve

from base.asyncio_demo.logger import get_logger
from base.common.observer import Signal

log = get_logger(__name__)


class WebappServer:
    def __init__(self):
        self._task: Optional[Task] = None
        self._terminator: Future = Future()
        self._clients: Set[WebSocketServerProtocol] = set()
        self._interface: Optional[Dict[str, Signal]] = None

    def __enter__(self):
        self._task = asyncio.create_task(self._serve())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._terminator.done()
        # self._task.cancel()

    def set_interface(self, interface) -> None:
        self._interface = interface

    async def _handler(self, websocket: WebSocketServerProtocol):
        self._clients.add(websocket)
        async for message in websocket:
            command = json.loads(message)
            topic = command.get("topic")
            print(topic)
            await self._interface.get(topic).emit()
            await websocket.send(f"ACK {topic}")

    async def _serve(self):
        async with serve(self._handler, "localhost", 8765):
            await self._terminator

    async def send(self, message: object) -> None:
        print(f"{message} -> {self._clients}")
        await asyncio.gather(*(client.send(json.dumps(message)) for client in self._clients))


async def main():
    with WebappServer() as server:
        server.set_interface(
            {
                "pause_shutdown_timer": Signal(),
                "resume_shutdown_timer": Signal(),
            }
        )
        for i in range(10**6):
            await asyncio.sleep(5)
            await server.send({"topic": "shutdown_timer_state", "data": {"seconds": i}})


if __name__ == "__main__":
    asyncio.run(main())
