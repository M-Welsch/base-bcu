from __future__ import annotations

from pathlib import Path

VIRTUAL_FILESYSTEM_IMAGE = Path("test/utils/backup_environment/virtual_hard_drive")
VIRTUAL_FILESYSTEM_MOUNTPOINT = Path("/tmp/base_tmpfs_mntdir")
NFS_SHARE_ROOT = Path("/tmp/base_tmpshare")  # fixme: deprecated?
SMB_MOUNTPOINT = Path("/tmp/base_tmpshare_mntdir")  # Fixme: deprecated?
NFS_MOUNTPOINT = Path("/tmp/base_nfs_mntdir")
