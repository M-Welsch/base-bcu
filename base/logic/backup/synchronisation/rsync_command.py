from pathlib import Path

from base.common.config import get_config


class RsyncCommand:
    def __init__(self) -> None:
        self._sync_config = get_config("sync.json")
        self._nas_config = get_config("nas.json")

    def compose(self, local_target_location: Path, source_location: Path, dry: bool = False) -> str:
        cmd = "rsync -avH --outbuf=N --info=progress2 --stats --delete"  # stats are important for the bu increment size
        cmd += " " + self._protocol_specific(local_target_location, source_location)
        cmd += " " + self._dry_run(dry)
        return cmd

    def _protocol_specific(self, local_target_location: Path, source_location: Path) -> str:
        if self._sync_config.protocol == "smb":
            return f"{source_location.as_posix()}/. {local_target_location}"
        else:
            return f'-e "ssh -i {self._sync_config.ssh_keyfile_path}" {self._nas_config.ssh_user}@{self._nas_config.ssh_host}:{source_location.as_posix()}/. {local_target_location}'

    @staticmethod
    def _dry_run(dry: bool) -> str:
        return "--dry-run" if dry else ""
