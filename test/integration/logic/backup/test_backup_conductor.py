from pathlib import Path
from typing import Generator, Tuple

import pytest

from base.logic.backup.backup_conductor import BackupConductor
from base.logic.network_share import NetworkShare
from test.integration.logic.backup.utils import prepare_source_sink_dirs, temp_source_sink_dirs
from test.utils import patch_multiple_configs, patch_config


def maintainance_mode_is_on() -> bool:
    return False


@pytest.fixture
def backup() -> Generator[Backup, None, None]:
    patch_multiple_configs(
        BackupConductor,
        {
            "backup.json": {},
            "sync.json": {
                "protocol": "smb"
            }
         }
    )
    yield BackupConductor(maintainance_mode_is_on)


def test_backup_conductor(backup_conductor: BackupConductor, temp_source_sink_dirs: Tuple[Path, Path]) -> None:
    src, sink = temp_source_sink_dirs
    prepare_source_sink_dirs(src_path=src, sink_path=sink, amount_files_in_src=2)
    patch_config(
        NetworkShare,
        {"local_nas_hdd_mount_point": ""}
    )
    backup_conductor.run()
