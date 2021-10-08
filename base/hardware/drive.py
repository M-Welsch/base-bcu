from pathlib import Path
from subprocess import PIPE, Popen, run
from time import sleep
from typing import Optional
from typing.io import IO

from base.common.config import Config
from base.common.drive_inspector import PartitionInfo
from base.common.exceptions import BackupPartitionError, ExternalCommandError, MountError, UnmountError
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
        self._partition_info = self._get_partition_info_or_raise()
        if not self._partition_info.mount_point:
            self._mount_backup_partition_or_raise(self._partition_info)
        LOG.info(f"Mounted HDD {self._partition_info.path} at {self._config.backup_hdd_mount_point}")
        self._available = HddState.available
        self._backup_browser.update_backup_list()

    def unmount(self) -> None:
        try:
            LOG.debug("Unmounting drive")
            self._unmount_backup_hdd_or_raise()
        except UnmountError:
            LOG.warning(f"Unmounting didn't work: {UnmountError}")
        except RuntimeError:
            LOG.warning(f"Unmounting didn't work: {RuntimeError}")

    @property
    def is_mounted(self) -> bool:
        return Path(self._config.backup_hdd_mount_point).is_mount()

    @property
    def is_available(self) -> HddState:
        return self._available

    def _get_partition_info_or_raise(self) -> PartitionInfo:
        try:
            return FileSystemWatcher(self._config.backup_hdd_spinup_timeout).backup_partition_info()
        except BackupPartitionError as e:
            LOG.error("Backup HDD not found!")
            self._available = HddState.not_available
            raise e

    def _mount_backup_partition_or_raise(self, partition_info: PartitionInfo) -> None:
        try:
            call_mount_command(
                partition_info.path, Path(self._config.backup_hdd_mount_point), self._config.backup_hdd_file_system
            )
        except MountError as e:
            LOG.error("Backup HDD could not be mounted!")
            self._available = HddState.not_available
            raise e

    def _unmount_backup_hdd_or_raise(self) -> None:
        LOG.debug("Trying to unmount backup HDD...")
        for i in range(self._config.backup_hdd_unmount_trials):
            try:
                call_unmount_command(self._config.backup_hdd_mount_point)
                return
            except UnmountError as e:
                LOG.warning(
                    f"Couldn't unmount BackupHDD after {i+1} trials. "
                    f"Waiting for {self._config.backup_hdd_unmount_waiting_secs}s and try again. Error: {e}"
                )
            sleep(self._config.backup_hdd_unmount_waiting_secs)
        LOG.warning(
            f"Couldn't unmount BackupHDD within {self._config.backup_hdd_unmount_trials} trials and waiting "
            f"for {self._config.backup_hdd_unmount_waiting_secs}s between trials."
        )
        raise UnmountError

    def space_used_percent(self) -> int:
        if self._partition_info:
            mount_point = self._config.backup_hdd_mount_point
            command = ["df", "--output=pcent", mount_point]
            LOG.debug(f"obtaining space used on bu hdd with command: {command}")
            try:
                proc = Popen(command, stdout=PIPE, stderr=PIPE)
                assert proc.stdout is not None
                # LOG.info(f"Space used on Backup HDD: {space_used}%")
            except FileNotFoundError:
                LOG.debug(f"FileNotFound during 'space_used_percent' with command {command}")
                return 0
            except TypeError:
                LOG.debug(f"Retrival of used space not possible yet. Mounting still in progress")
                return 0
            try:
                space_used = int(self._extract_space_used_from_output(proc.stdout))
            except IndexError:
                LOG.debug(f"IndexError during 'space_used_percent' with command {command}")
                space_used = 0
            except ValueError:
                LOG.debug(f"Value Error during 'space_used_percent' with command {command}")
                space_used = 0

            if space_used is not None:
                return space_used
        LOG.debug("no partition info in 'space_used_percent'")
        return 0

    def _extract_space_used_from_output(self, df_output: IO[bytes]) -> float:
        df_output_str = self._get_string_from_df_output(df_output)
        space_used_percentage = self._remove_heading_from_df_output(df_output_str)
        return space_used_percentage

    @staticmethod
    def _get_string_from_df_output(df_output: IO[bytes]) -> str:
        return str(df_output.read().decode())

    @staticmethod
    def _remove_heading_from_df_output(df_output_str: str) -> float:
        string = "".join(x for x in df_output_str if x.isdigit())
        return float(string) if string else 0


def call_mount_command(partition: str, mount_point: Path, file_system: str) -> None:
    command = [f"mount", "-t", str(file_system), str(partition), str(mount_point)]
    LOG.debug(" ".join(command))
    cp = run(command, stdout=PIPE, stderr=PIPE)
    if cp.stderr:
        raise MountError(f"Partition could not be mounted: {str(cp.stderr)}")


def call_unmount_command(mount_point: Path) -> None:
    command = ["sudo", "umount", str(mount_point)]
    LOG.debug(" ".join(command))
    cp = run(command, stdout=PIPE, stderr=PIPE)
    if cp.stderr:
        raise UnmountError(f"Partition could not be unmounted: {str(cp.stderr)}")
