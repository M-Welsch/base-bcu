from os import path
from time import sleep
from subprocess import run, PIPE

from base.common.config import Config
from base.common.exceptions import MountingError, UnmountError, ExternalCommandError
from base.common.drive_inspector import DriveInspector
from base.common.file_system import FileSystemWatcher
from base.common.logger import LoggerFactory


LOG = LoggerFactory.get_logger(__name__)


class Drive:
    def __init__(self):
        self._config = Config("drive.json")
        self._partition_info = None

    @property
    def backup_hdd_device_info(self):
        return self._partition_info

    def mount(self):
        LOG.debug("Mounting drive")
        file_system_watcher = FileSystemWatcher(self._config.backup_hdd_spinup_timeout)
        file_system_watcher.add_watches(["/dev"])
        self._partition_info = file_system_watcher.backup_partition_info()
        if self._partition_info is None:
            raise MountingError(f"Backup HDD not available!")
        if self._partition_info.mount_point is None:
            command = ["mount", "-t", self._config.backup_hdd_file_system,
                       self._partition_info.path, self._config.backup_hdd_mount_point]
            try:
                LOG.debug(command)
                run_external_command(command)
                LOG.info(f"Mounted HDD {self._partition_info.path} at {self._config.backup_hdd_mount_point}")
            except ExternalCommandError:
                raise MountingError(f"Backup HDD could not be mounted")
        assert DriveInspector().backup_partition_info.mount_point

    def unmount(self):
        try:
            LOG.debug("Unmounting drive")
            self._unmount_backup_hdd()
        except UnmountError:
            LOG.error(f"Unmounting didnt work: {UnmountError}")
        except RuntimeError:
            LOG.error(f"Unmounting didnt work: {RuntimeError}")

    @property
    def is_mounted(self):
        return path.ismount(self._config.backup_hdd_mount_point)

    # Todo: cleanup this mess
    def _unmount_backup_hdd(self):
        LOG.debug("Trying to unmount backup HDD...")
        command = ["sudo", "umount", self._config.backup_hdd_mount_point]
        unmount_trials = 0
        unmount_success = False
        while unmount_trials < 5 and not unmount_success:
            try:
                run_external_command(command)
                unmount_success = True
            except ExternalCommandError as e:
                if "not mounted" in str(e):
                    LOG.warning(f"BackupHDD already unmounted. stderr: {e}")
                    unmount_success = True
                # Todo: find out who accesses the drive right now and write into logfile (with lsof?)
                sleep(1)
                unmount_trials += 1
                if unmount_trials == 5:
                    LOG.warning(f"Couldn't unmount BackupHDD within 5 trials. Error: {e}")
                    if "target is busy" in str(e):
                        raise UnmountError(e)
                    else:
                        raise RuntimeError


def run_external_command(command):
    cp = run(command, stdout=PIPE, stderr=PIPE)
    if cp.stderr:
        raise ExternalCommandError(cp.stderr)
