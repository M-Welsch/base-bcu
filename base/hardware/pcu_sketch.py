import asyncio
from dataclasses import dataclass
from time import time
from enum import Enum, auto
from typing import Optional, Dict, Callable


class PcuRequest(Enum):
    ...


class Returncode(Enum):
    SUCCESS = auto()
    FAIL = auto()
    BCU_TIMEOUT = auto()
    PCU_TIMEOUT = auto()


@dataclass
class PcuResponse:
    returncode: Returncode
    request: PcuRequest
    payload: str


class PcuPushNotification(Enum):
    BUTTON0_PRESSED: auto()
    BUTTON1_PRESSED: auto()
    SYSTEM_UNDERVOLTAGE: auto()


TIMEOUT = 0.3


class Pcu:
    flag_running = True
    __current_request: Optional[PcuRequest] = None
    __current_response: Optional[PcuResponse] = None

    def __init__(self, callbacks: Dict[PcuPushNotification, Callable]):
        self._callbacks = callbacks

    async def run(self) -> None:
        """ starts the pcu interface. This is a task.

        runs a semi-infinite loop, that checks at each run for commands is requested.
        If so, it runs the command and takes the "answer" from the pcu. If not, it waits some time for an unrequested
        incoming message and takes it as an "answer"

        Parses an answer into either a PcuResponse object (if associated with a command) or calls a callback in case of
        a push notification
        """
        while self.flag_running:
            if self.__current_request is not None:
                pcu_answer = await self._issue_request(self.__current_request)
            else:
                pcu_answer = await self._listen_for_unrequested_messages()
            if pcu_answer is not None:
                self.__current_response = self._parse_pcu_answer(pcu_answer)
            await asyncio.sleep(0.01)

    async def command(self, request: PcuRequest) -> PcuResponse:
        """ enqueues a command and waits for its response """
        self.__current_request = request
        start = time()
        while self.__current_response is None:
            if time() - start > TIMEOUT:
                return PcuResponse(returncode=Returncode.BCU_TIMEOUT, payload="", request=request)
            await asyncio.sleep(0.01)
        self.__current_response: PcuResponse
        return_response = PcuResponse(
            returncode=self.__current_response.returncode,
            payload=self.__current_response.payload,
            request=request
        )
        self.__current_request = None
        self.__current_response = None
        return return_response

    def terminate(self) -> None:
        self.flag_running = False

    def _parse_pcu_answer(self, pcu_answer: str) -> Optional[PcuResponse]:
        """ parses a raw string from the PCU. It tries to parse it into a PcuResponse object.
        If it finds a push-notification, it runs the associated callback function"""
        response = self._parse_pcu_response(pcu_answer)
        push_notification = self._parse_push_notification(pcu_answer)
        if push_notification is not None:
            self._callbacks[push_notification]()
        return response

    def _parse_pcu_response(self, pcu_answer: str) -> Optional[PcuResponse]:
        """ tries to parse the raw pcu_answer into a PcuResponse object. Returns None on fail"""
        ...

    def _parse_push_notification(self, pcu_answer: str) -> Optional[PcuPushNotification]:
        """ tries to find a push notification in the pcu_answer and parses it into a PcuPushNotification object"""
        ...

    async def _issue_request(self, request: PcuRequest) -> str:
        """ sends a command to the pcu and waits for a response. The response
        will be parsed and returned as a PcuResponse Object"""
        return "blabla"

    async def _listen_for_unrequested_messages(self) -> str:
        """ listen for an unrequested message from the pcu for some time. If one is received
        it gets parsed and returned as a PcuResponse Object"""
        return "bla bla bla"