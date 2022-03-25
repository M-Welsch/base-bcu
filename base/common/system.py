import subprocess
from pathlib import Path
from subprocess import PIPE, Popen, call
from typing import Dict, List

from base.common.constants import BackupDirectorySuffix
from base.common.exceptions import BackupSizeRetrievalError, ExternalCommandError
from base.common.logger import LoggerFactory
from base.logic.backup.synchronisation.rsync_command import RsyncCommand

LOG = LoggerFactory.get_logger(__name__)


class System:
    @staticmethod
    def size_of_next_backup(local_target_location: Path, source_location: Path) -> int:
        """Return size of next backup increment in bytes."""
        cmd = RsyncCommand().compose(local_target_location, source_location, dry=True)
        # the command HAS to run in the shell because of the /* behind the source directory
        # moreover the command must be a string, not a list
        LOG.info(f"estimating size of new backup with: {cmd}")
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
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
    def mount_smb_share(mount_point: str) -> subprocess.Popen:
        command = f"mount {mount_point}".split()
        LOG.info(f"mount datasource with command: {command}")
        return Popen(command, bufsize=0, stderr=PIPE, stdout=PIPE)
