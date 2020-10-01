from base.common.config import Config
from base.common.base_logging import Logger
from base.common.tcp import TCPServerThread
from base.hwctrl.hwctrl import HWCTRL
from base.webapp.webapp import Webapp
from base.schedule.scheduler import BaseScheduler
from base.backup.backup import BackupManager
from base.daemon.mounting import MountManager
from base.common.utils import *
from base.common.readout_hdd_parameters import readout_parameters_of_all_hdds
from base.sbu_interface.sbu_updater import *


class BaseUpdater:
    def __init__(self):
        self._sbu_updater = SbuUpdater()
        self._display = Display()

    def update_all(self):
        self._terminate_base()
        self._update_base()
        self._update_sbu()
        self._reboot()

    def _terminate_base(self):
        self._display.write("Terminating", "BaSe Service")
        raise NotImplementedError

    def _update_base(self):
        self._display.write("Getting new", "Files ...")
        self._get_new_files_from_repo()
        raise NotImplementedError

    def _get_new_files_from_repo(self):
        # Todo: git pull @branch release or stable or ... tbd
        pass

    def _update_sbu(self):
        raise NotImplementedError

    def _reboot(self):
        raise NotImplementedError


if __name__ == '__main__':
    BU = BaseUpdater()
    BU.update_all()