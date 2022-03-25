import subprocess
from pathlib import Path
from subprocess import PIPE, Popen
from typing import List, IO

from base.common.exceptions import BackupSizeRetrievalError, NetworkError
from base.common.logger import LoggerFactory
from base.logic.backup.synchronisation.rsync_command import RsyncCommand

LOG = LoggerFactory.get_logger(__name__)


class System:
    @staticmethod
    def size_of_next_backup(local_target_location: Path, source_location: Path) -> int:
        """Return size of next backup increment in bytes."""
        cmd = RsyncCommand().compose(local_target_location, source_location, dry=True)
        LOG.info(f"estimating size of new backup with: {cmd}")
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        p.wait()
        try:
            lines: List[str] = [
                l.decode() for l in p.stdout.readlines() if l.startswith(b"Total transferred file size")  # type: ignore
            ]
            line = lines[0]
            return int("".join(c for c in line if c.isdigit()))
        except (IndexError, ValueError, AttributeError) as e:
            if p.stderr:
                LOG.error("\n".join([str(l) for l in p.stderr.read()]))
            raise BackupSizeRetrievalError from e

    @staticmethod
    def copy_newest_backup_with_hardlinks(recent_backup: Path, new_backup: Path) -> subprocess.Popen:
        copy_command = f"cp -al {recent_backup}/* {new_backup}"
        LOG.info(f"copy command: {copy_command}")
        return Popen(copy_command, bufsize=0, shell=True, stdout=PIPE, stderr=PIPE)

    @staticmethod
    def free_space(backup_target: Path) -> int:
        """returns free space on backup hdd in bytes"""

        def _remove_heading_from_df_output(df_output: IO[bytes]) -> int:
            return int(list(df_output)[-1].decode().strip())

        command: List[str] = ["df", "--output=avail", backup_target.as_posix()]
        out = Popen(command, stdout=PIPE, stderr=PIPE)
        out.wait()
        if out.stderr is not None:
            stderr_lines = out.stderr.readlines()
            if stderr_lines:
                raise BackupSizeRetrievalError(
                    f"Cannot obtain free space on backup hdd: {[stderr_line.decode().strip() for stderr_line in stderr_lines]}"
                )
        free_space_on_bu_hdd = _remove_heading_from_df_output(out.stdout)  # type: ignore
        LOG.info(f"obtaining free space on bu hdd with command: {' '.join(command)}. Received {free_space_on_bu_hdd}")
        return free_space_on_bu_hdd


class SmbShareMount:
    def mount_smb_share(self, mount_point: str) -> None:
        command = f"mount {mount_point}".split()
        LOG.info(f"mount datasource with command: {command}")
        self._parse_process_output(self.run_command(command))

    def unmount_smb_share(self, mount_point: str) -> None:
        command = f"umount {mount_point}".split()
        LOG.info(f"unmount datasource with command: {command}")
        self._parse_process_output(self.run_command(command))

    @staticmethod
    def run_command(command: List[str]) -> Popen:
        return Popen(command, bufsize=0, stdout=PIPE, stderr=PIPE)

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
