from base.logic.sync import RsyncWrapperThread


class Backup:
    def __init__(self):
        self._sync = RsyncWrapperThread(set_backup_finished_flag=None)
