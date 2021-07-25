from os import path
from subprocess import PIPE, Popen, run
from time import sleep
from typing import List, Optional
from typing.io import IO

from base.common.config import Config
from base.common.drive_inspector import DriveInspector, PartitionInfo
from base.common.exceptions import ExternalCommandError, MountingError, UnmountError
from base.common.file_system import FileSystemWatcher
from base.common.logger import LoggerFactory
from base.common.status import HddState
from base.logic.backup.backup_browser import BackupBrowser

LOG = LoggerFactory.get_logger(__name__)


class Drive:
    def __init__(self, backup_browser: BackupBrowser):
        self._backup_browser: BackupBrowser = backup_browser
        self._config: Config = Config("drive.json")
        self._partition_info: Optional[PartitionInfo] = None
        self._available: HddState = HddState.unknown

    @property
    def backup_hdd_device_info(self) -> Optional[PartitionInfo]:
        return self._partition_info

    def mount(self) -> None:
        LOG.debug("Mounting drive")
        file_system_watcher = FileSystemWatcher(self._config.backup_hdd_spinup_timeout)
        file_system_watcher.add_watches(["/dev"])
        self._partition_info = file_system_watcher.backup_partition_info()
        if self._partition_info is None:
            LOG.error("Backup HDD not found!")
            self._available = HddState.not_available
            raise MountingError(f"Backup HDD not available!")
        if self._partition_info.mount_point is None:
            command = [
                "mount",
                "-t",
                str(self._config.backup_hdd_file_system),
                str(self._partition_info.path),
                str(self._config.backup_hdd_mount_point),
            ]
            try:
                LOG.debug(command)
                run_external_command(command)
                LOG.info(f"Mounted HDD {self._partition_info.path} at {self._config.backup_hdd_mount_point}")
            except ExternalCommandError:
                self._available = HddState.not_available
                raise MountingError(f"Backup HDD could not be mounted")
        assert DriveInspector().backup_partition_info.mount_point
        self._backup_browser.update_backup_list()
        self._available = HddState.available

    def unmount(self) -> None:
        try:
            LOG.debug("Unmounting drive")
            self._unmount_backup_hdd()
        except UnmountError:
            LOG.error(f"Unmounting didn't work: {UnmountError}")
        except RuntimeError:
            LOG.error(f"Unmounting didn't work: {RuntimeError}")

    @property
    def is_mounted(self) -> bool:
        return path.ismount(self._config.backup_hdd_mount_point)

    @property
    def is_available(self) -> HddState:
        return self._available

    # Todo: cleanup this mess
    def _unmount_backup_hdd(self) -> None:
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

    def space_used_percent(self) -> float:
        if self._partition_info:
            mount_point = Config("drive.json").backup_hdd_mount_point
            command = ["df", "--output=pcent", mount_point]
            LOG.debug(f"obtaining space used on bu hdd with command: {command}")
            try:
                proc = Popen(command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=PIPE)
                assert proc.stdout is not None
                space_used = float(self._remove_heading_from_df_output(proc.stdout))
                # LOG.info(f"Space used on Backup HDD: {space_used}%")
            except ValueError:
                LOG.debug(f"Value Error during 'space_used_percent' with command {command}")
                space_used = 0
            except FileNotFoundError:
                LOG.debug(f"FileNotFound during 'space_used_percent' with command {command}")
                space_used = 0
            except IndexError:
                LOG.debug(f"IndexError during 'space_used_percent' with command {command}")
                space_used = 0
            except TypeError:
                LOG.debug(f"Retrival of used space not possible yet. Mounting still in progress")
                space_used = 0
            if space_used is not None:
                return space_used
        LOG.debug("no partition info in 'space_used_percent'")
        return 0

    @staticmethod
    def _remove_heading_from_df_output(df_output: IO[str]) -> str:
        return [item.split("%")[0] for item in df_output if not item.strip() == "Use%"][0]


def run_external_command(command: List[str]) -> None:
    cp = run(command, stdout=PIPE, stderr=PIPE)
    if cp.stderr:
        raise ExternalCommandError(cp.stderr)
