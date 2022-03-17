from __future__ import annotations

from pathlib import Path

VIRTUAL_FILESYSTEM_IMAGE = Path("test/utils/backup_environment/virtual_hard_drive")
VIRTUAL_FILESYSTEM_MOUNTPOINT = Path("/tmp/base_tmpfs_mntdir")
SMB_SHARE_ROOT = Path("/tmp/base_tmpshare")
SMB_MOUNTPOINT = Path("/tmp/base_tmpshare_mntdir")