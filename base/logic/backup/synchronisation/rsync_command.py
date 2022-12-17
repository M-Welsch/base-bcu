from pathlib import Path
from typing import List

from base.common.config import get_config
from base.logic.backup.protocol import Protocol


class RsyncCommand:
    def __init__(self) -> None:
        self._sync_config = get_config("sync.json")
        self._nas_config = get_config("nas.json")
        self._protocol = Protocol(self._sync_config.protocol)

    def compose(self, local_target_location: Path, source_location: Path, dry: bool = False) -> List[str]:
        """compose the rsync command for a specific protocol
        ssh: rsync <nas-ip>::<name-of-share>/* <backup-target-location> --port=<rsync-daemon-port> <common-params>
        nfs: rsync <source-location>/. <common-params>

        common-params = --delete --stats -aH --info=progress2

        Examples:
        ssh: rsync 192.168.0.2::backup_source/* /mnt/BackupHDD/smnth --port=1234 --delete --stats -aH --info=progress2
        nfs: rsync /mnt/NASHDD/backup_source/* /mnt/BackupHDD/smnth --delete --stats -aH --info=progress2

        Hints:
        - <name-of-share> is defined in /etc/rsyncd and points to some location in the file system"""
        cmd = ["rsync", "-aH", "--stats", "--delete", "--info=progress2"]
        if dry:
            cmd.append("--dry")
        if self._protocol == Protocol.SSH:
            ip = self._nas_config["ssh_host"]
            rsync_share = self._sync_config["rsync_share_name"]
            rsync_port = self._sync_config["rsync_daemon_port"]
            cmd.extend([f"{ip}::{rsync_share}/*", local_target_location.as_posix(), f"--port={rsync_port}"])
        elif self._protocol == Protocol.NFS:
            cmd.extend([f"{source_location.as_posix()}/*", local_target_location.as_posix()])
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
