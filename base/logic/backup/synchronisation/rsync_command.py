from pathlib import Path
from typing import List

from base.common.config import get_config
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class RsyncCommand:
    def __init__(self) -> None:
        self._sync_config = get_config("sync.json")
        self._nas_config = get_config("nas.json")

    def compose(self, local_target_location: Path, source_location: Path, dry: bool = False) -> List[str]:
        cmd = "sudo rsync -avH --outbuf=N --info=progress2".split()
        cmd.extend(self._protocol_specific(local_target_location, source_location))
        cmd.extend(self._dry_run(dry))
        LOG.info(f"About to sync with: {cmd}")
        return cmd

    def _protocol_specific(self, local_target_location: Path, source_location: Path) -> List[str]:
        if self._sync_config.protocol == "smb":
            return f"{source_location}/ {local_target_location}".split()
        else:
            return [
                "-e",
                f"ssh -i {self._sync_config.ssh_keyfile_path}",
                f"{self._nas_config.ssh_user}@{self._nas_config.ssh_host}:{source_location}/",
                f"{local_target_location}",
            ]

    @staticmethod
    def _dry_run(dry: bool) -> List[str]:
        return ["--dry-run"] if dry else [""]
