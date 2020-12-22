import logging
from pathlib import Path

from base.logic.sync import RsyncWrapperThread


LOG = logging.getLogger(Path(__file__).name)


class Backup:
    def __init__(self):
        self._sync = RsyncWrapperThread(set_backup_finished_flag=None)
        LOG.info("Backup initialized")

    def on_backup_request(self, **kwargs):
        LOG.info("Backup request received")
