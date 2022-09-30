from pathlib import Path
from typing import List

from base.common.config import get_config
from base.logic.backup.protocol import Protocol


class RsyncCommand:
    def __init__(self) -> None:
        self._sync_config = get_config("sync.json")
        self._nas_config = get_config("nas.json")
        self._protocol = Protocol(self._sync_config.protocol)

    def compose(self, local_target_location: Path, source_location: Path, dry: bool = False) -> str:
        cmd = "rsync -avH --outbuf=N --info=progress2 --stats --delete"  # stats are important for the bu increment size
        cmd += " " + self._protocol_specific(local_target_location, source_location)
        cmd += " " + self._dry_run(dry)
        return cmd

    def compose_list(self, local_target_location: Path, source_location: Path, dry: bool = False) -> List[str]:
        if self._protocol in [Protocol.SMB, Protocol.NFS]:
            cmd = [
                "rsync",
                "-aH",
                "--stats",
                "--delete",
                f"{source_location.as_posix()}/.",
                local_target_location.as_posix(),
            ]
        else:
            cmd = [
                "rsync",
                "-aH",
                "--stats",
                "--delete",
                f"{self._nas_config.ssh_host}::{source_location.as_posix()}/.",
                local_target_location.as_posix(),
            ]
        if dry:
            cmd.append("--dry-run")
        return cmd

    def _protocol_specific(self, local_target_location: Path, source_location: Path) -> str:
        if self._protocol in [Protocol.SMB, Protocol.NFS]:
            return f"{source_location.as_posix()}/. {local_target_location}"
        else:
            return f'-e "ssh -i {self._sync_config.ssh_keyfile_path}" {self._nas_config.ssh_host}::{source_location.as_posix()}/. {local_target_location}'

    @staticmethod
    def _dry_run(dry: bool) -> str:
        return "--dry-run" if dry else ""
