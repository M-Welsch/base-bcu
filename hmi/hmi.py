from base.common.config import Config
from base.hmi.display import Display
from base.sbu_interface.sbu_communicator import SbuCommunicator

class HumanMachineInterface:
    def __init__(self):
        self._sbu_communicator = SbuCommunicator.global_instance()
        self._display = Display(self._sbu_communicator)