import os, sys
path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

from base.common.config import Config
from base.common.base_logging import Logger
from base.common.tcp import TCPClientInterface
from base.hwctrl.hwctrl import HWCTRL
from base.hwctrl.display import *
from base.common.utils import *
from base.sbu_interface.sbu_communicator import *
from base.sbu_interface.sbu_updater import *
from sysdmanager import SystemdManager


class BaseUpdater:
    def __init__(self):
        pass

    def update_all(self):
        self._terminate_base()
        self._take_over_display()
        self._update_base()
        self._give_back_serial_connection()
        self._update_sbu()
        self._reboot()

    def _terminate_base(self):
        tcp_port_orig = self._get_tcp_port()
        tcp_port = tcp_port_orig
        sysdmanager = SystemdManager()
        if sysdmanager.is_active("base.service"):

            while tcp_port <= (tcp_port_orig + 2):
                try:
                    tcpClient = TCPClientInterface(port=tcp_port)
                    answer = tcpClient.send("terminate_daemon")
                    print(answer)
                except ConnectionRefusedError:
                    tcp_port += 1
                    print(f"TCP-Server couldn't establish connection on port {tcp_port}")
        else:
            print("BaSe already down")

    def _get_tcp_port(self):
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._config = Config(path+"/config.json")
        return self._config.tcp_port

    def _take_over_display(self):
        self._logger = Logger("/home/base/base/log", "base-updater")
        self._hwctrl = HWCTRL(self._config.hwctrl_config, self._logger)
        self._sbuc = SbuCommunicator(self._hwctrl, self._logger, self._config.sbu_communicator_config)
        self._display = Display(self._hwctrl, self._sbuc, self._config)

    def _update_base(self):
        self._display.write("Getting new", "Files ...")
        self._get_new_files_from_repo()

    def _get_new_files_from_repo(self):
        # Todo: git pull @branch release or stable or ... tbd
        pass

    def _give_back_serial_connection(self):
        self._sbuc.terminate()

    def _update_sbu(self):
        self._hwctrl.enable_receiving_messages_from_attiny()
        self._hwctrl.set_attiny_serial_path_to_sbc_fw_update()

        SbuU = SbuUpdater()
        SbuU.update_sbu()

        self._hwctrl.disable_receiving_messages_from_attiny()
        self._hwctrl.set_attiny_serial_path_to_communication()

    def _reboot(self):
        self._hwctrl.terminate()
        self._logger.terminate()
        #shutdown_bcu()


if __name__ == '__main__':
    BU = BaseUpdater()
    BU.update_all()