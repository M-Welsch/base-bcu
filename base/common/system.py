import subprocess
from pathlib import Path
from subprocess import PIPE, Popen, run
from time import sleep, time
from typing import List

from base.common.exceptions import BackupSizeRetrievalError, NetworkError, TimeSynchronisationError
from base.common.logger import LoggerFactory
from base.logic.backup.synchronisation.rsync_command import RsyncCommand

LOG = LoggerFactory.get_logger(__name__)


class System:
    @staticmethod
    def size_of_next_backup(local_target_location: Path, source_location: Path) -> int:
        """Return size of next backup increment in bytes."""
        cmd = RsyncCommand().compose_list(local_target_location, source_location, dry=True)
        LOG.info(f"estimating size of new backup with: {cmd}")
        p = run(cmd, capture_output=True)
        stdout_lines = p.stdout.decode().split("\n")
        try:
            relevant_line = [l for l in stdout_lines if l.startswith("Total transferred file size")][0]
            return int("".join(c for c in relevant_line if c.isdigit()))
        except (IndexError, ValueError, AttributeError) as e:
            stderr_lines = p.stderr.decode()
            LOG.error(stderr_lines)
            raise BackupSizeRetrievalError from e

    @staticmethod
    def copy_newest_backup_with_hardlinks(recent_backup: Path, new_backup: Path) -> subprocess.Popen:
        copy_command = f"cp -al {recent_backup}/. {new_backup}"
        LOG.info(f"copy command: {copy_command}")
        # Popen here, because the 'run' automatically waits for the process to finish. Popen returns immediately
        return Popen(copy_command, bufsize=0, shell=True, stdout=PIPE, stderr=PIPE)

    @staticmethod
    def free_space(backup_target: Path) -> int:
        """returns free space on backup hdd in bytes"""

        def _remove_heading_from_df_output(df_output: bytes) -> int:
            return int(df_output.decode().strip().split("\n")[-1])

        command: List[str] = ["df", "--output=avail", backup_target.as_posix(), "-B 1"]
        out = run(command, capture_output=True)
        if out.stderr:
            raise BackupSizeRetrievalError(f"Cannot obtain free space on backup hdd: {out.stderr.decode()}")
        free_space_on_bu_hdd = _remove_heading_from_df_output(out.stdout)
        LOG.info(f"obtaining free space on bu hdd with command: {' '.join(command)}. Received {free_space_on_bu_hdd}")
        return free_space_on_bu_hdd

    def wait_for_ntp_update(self, timeout_seconds: float) -> None:
        start = time()
        while not self._system_clock_synchronized_with_ntp():
            if time() - start > timeout_seconds:
                raise TimeSynchronisationError(f"Waiting for NTP Update timed out (timeout = {timeout_seconds}s)")
            sleep(0.5)

    @staticmethod
    def _system_clock_synchronized_with_ntp() -> bool:
        timedate_status_raw = subprocess.check_output("timedatectl").decode()
        if "System clock synchronized: yes" in timedate_status_raw:
            return True
        elif "System clock synchronized: no" in timedate_status_raw:
            return False
        else:
            raise TimeSynchronisationError("NTP synchronisation status cannot be obtained!")


class NetworkShareMount:
    def mount(self, mount_point: str) -> None:
        command = f"mount {mount_point}".split()
        LOG.info(f"mount datasource with command: {command}")
        self._parse_process_output(self.run_command(command))

    def unmount(self, mount_point: str) -> None:
        command = f"umount {mount_point}".split()
        LOG.info(f"unmount datasource with command: {command}")
        self._parse_process_output(self.run_command(command))

    @staticmethod
    def run_command(command: List[str]) -> Popen:
        p = Popen(command, bufsize=0, stdout=PIPE, stderr=PIPE)
        p.wait()
        return p

    @staticmethod
    def _parse_process_output(process: Popen) -> None:
        if process.stdout is not None:
            for line in process.stdout.readlines():
                LOG.debug("stdout: " + line)
        if process.stderr is not None:
            for line in [line.decode() for line in process.stderr.readlines()]:
                if "error(16)" in line:
                    # Device or resource busy
                    LOG.warning(f"Device probably already (un)mounted: {line}")
                elif "error(2)" in line:
                    # No such file or directory
                    error_msg = f"Network share not available: {line}"
                    LOG.critical(error_msg)
                    raise NetworkError(error_msg)
                elif "could not resolve address" in line:
                    error_msg = f"Errant IP address: {line}"
                    LOG.critical(error_msg)
                    raise NetworkError(error_msg)
                else:
                    LOG.debug("stderr: " + line)
