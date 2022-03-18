from pathlib import Path
from test.utils.backup_environment.virtual_backup_environment import prepare_source_sink_dirs
from test.utils.patch_config import patch_config, patch_multiple_configs
from typing import Generator, Tuple

import pytest

from base.logic.backup.backup import Backup
from base.logic.backup.backup_conductor import BackupConductor
from base.logic.network_share import NetworkShare


def maintainance_mode_is_on() -> bool:
    return False


@pytest.fixture
def backup() -> Generator[Backup, None, None]:
    patch_multiple_configs(BackupConductor, {"backup.json": {}, "sync.json": {"protocol": "smb"}})
    yield BackupConductor(maintainance_mode_is_on)


def test_backup_conductor(backup_conductor: BackupConductor, temp_source_sink_dirs: Tuple[Path, Path]) -> None:
    src, sink = temp_source_sink_dirs
    prepare_source_sink_dirs(src=src, sink=sink, amount_files_in_src=2)
    patch_config(NetworkShare, {"local_nas_hdd_mount_point": ""})
    backup_conductor.run()
