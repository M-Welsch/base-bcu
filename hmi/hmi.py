from base.common.config import Config
from base.hmi.display import Display
from base.sbu_interface.sbu_communicator import SbuCommunicator


class HumanMachineInterface:
    def __init__(self):
        self._sbu_communicator = SbuCommunicator.global_instance()
        self._display = Display(self._sbu_communicator)

    def init_idle_menu(self):
        pass

    def write_priority_message_to_display(self, line1, line2):
        self._display.write(line1, line2)
