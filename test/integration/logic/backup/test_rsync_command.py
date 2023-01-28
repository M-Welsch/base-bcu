from subprocess import PIPE, Popen
from test.utils.backup_environment.virtual_backup_environment import BackupTestEnvironment
from test.utils.patch_config import patch_multiple_configs

import pytest

from base.logic.backup.protocol import Protocol
from base.logic.backup.synchronisation.rsync_command import RsyncCommand


@pytest.fixture(scope="class")
def backup_environment():
    with BackupTestEnvironment(
        protocol=Protocol.SSH,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
    ) as virtual_backup_env:
        yield virtual_backup_env


class TestComposition:
    @staticmethod
    @pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.NFS])
    def test_composition(protocol: Protocol, backup_environment: BackupTestEnvironment) -> None:
        backup_environment.create_testfiles(
            amount_files_in_source=(amount_files_in_source := 10),
            bytesize_of_each_sourcefile=1024,
        )
        backup_environment.mount_all()
        backup_env_configs = backup_environment.create()

        patch_multiple_configs(
            RsyncCommand, {"nas.json": backup_environment.nas_config, "sync.json": backup_environment.sync_config}
        )
        command = RsyncCommand().compose(backup_environment.sink, backup_environment.source_on_host)
        Popen(" ".join(command), shell=True).wait()
        assert len(list(backup_environment.sink.iterdir())) == amount_files_in_source
        for file in backup_environment.sink.iterdir():
            assert file.stat().st_size == 1024
