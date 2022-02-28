import shutil
from pathlib import Path
from test.utils import create_file_with_random_data, patch_multiple_configs

from py import path

from base.logic.backup.incremental_backup_preparator import IncrementalBackupPreparator
from base.logic.backup.synchronisation.rsync_command import RsyncCommand


def test_obtain_size_of_next_backup_increment(tmp_path: path.local) -> None:
    patch_multiple_configs(RsyncCommand, {"sync.json": {"protocol": "smb"}, "nas.json": {}})
    src = tmp_path / "src"
    sink = tmp_path / "sink"
    [pt.mkdir() for pt in [src, sink]]
    testfiles = [src / f"testfile{cnt}" for cnt in range(2)]
    bytesize_of_each_testfile = 1024
    [create_file_with_random_data(Path(testfile), size_bytes=bytesize_of_each_testfile) for testfile in testfiles]
    shutil.copy(testfiles[0], sink)
    size = IncrementalBackupPreparator._obtain_size_of_next_backup_increment(
        source_location=Path(src), local_target_location=Path(sink)
    )
    assert size == bytesize_of_each_testfile
