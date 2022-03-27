from pathlib import Path
from subprocess import PIPE, Popen, run
from time import sleep, time
from typing import Optional
from typing.io import IO

from base.common.config import Config, get_config
from base.common.exceptions import BackupHddNotAvailable, MountError, UnmountError
from base.common.logger import LoggerFactory
from base.common.status import HddState

LOG = LoggerFactory.get_logger(__name__)


class Drive:
    def __init__(self) -> None:
        self._config: Config = get_config("drive.json")
        self._available: HddState = HddState.unknown

    def mount(self) -> None:
        """udev recognizes the correct drive and creates a symlink to /dev/BACKUPHDD"""
        LOG.debug("Mounting drive")
        self._wait_for_backup_hdd()
        call_mount_command()
        LOG.info(f"Mounted /dev/BACKUPHDD at {self._config.backup_hdd_mount_point}")
        self._available = HddState.available

    def unmount(self) -> None:
        try:
            LOG.debug("Unmounting drive")
            self._unmount_backup_hdd_or_raise()
        except (UnmountError, RuntimeError) as e:
            LOG.warning(f"Unmounting didn't work: {UnmountError}")
            raise UnmountError from e

    def _wait_for_backup_hdd(self) -> None:
        time_start = time()
        while not Path("/dev/BACKUPHDD").exists():
            if time() - time_start > self._config.backup_hdd_spinup_timeout:
                raise BackupHddNotAvailable
            sleep(0.5)

    @property
    def is_mounted(self) -> bool:
        return Path(self._config.backup_hdd_mount_point).is_mount()

    @property
    def is_available(self) -> HddState:
        return self._available

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
        space_used = 0
        if self.is_mounted:
            mount_point = self._config.backup_hdd_mount_point
            command = ["df", "--output=pcent", mount_point]
            LOG.debug(f"obtaining space used on bu hdd with command: {command}")
            try:
                proc = Popen(command, stdout=PIPE, stderr=PIPE)
                assert proc.stdout is not None
                space_used = int(self._extract_space_used_from_output(proc.stdout))
            except FileNotFoundError:
                LOG.debug(f"FileNotFound during 'space_used_percent' with command {command}")
            except TypeError:
                LOG.debug(f"Retrival of used space not possible yet. Mounting still in progress")
            except IndexError:
                LOG.debug(f"IndexError during 'space_used_percent' with command {command}")
            except ValueError:
                LOG.debug(f"Value Error during 'space_used_percent' with command {command}")
        LOG.debug("not mounted")
        return space_used

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


def call_mount_command() -> None:
    command = "mount /dev/BACKUPHDD"
    LOG.debug(f"Mounting with {command}")
    cp = run(command.split(), stdout=PIPE, stderr=PIPE)
    if cp.stderr:
        raise MountError(f"Partition could not be mounted: {str(cp.stderr)}")


def call_unmount_command(mount_point: Path) -> None:
    command = f"umount {mount_point.as_posix()}"
    LOG.debug(f"Unmounting with {command}")
    cp = run(command.split(), stdout=PIPE, stderr=PIPE)
    if cp.stderr:
        raise UnmountError(f"Partition could not be unmounted: {str(cp.stderr)}")
