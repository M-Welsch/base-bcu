from subprocess import PIPE, Popen
from test.utils.backup_environment.virtual_backup_environment import BackupTestEnvironment
from test.utils.patch_config import patch_multiple_configs

import pytest

from base.logic.backup.protocol import Protocol
from base.logic.backup.synchronisation.rsync_command import RsyncCommand


@pytest.mark.parametrize("protocol", [Protocol.NFS])
def test_composition(protocol: Protocol) -> None:
    with BackupTestEnvironment(
        protocol=protocol,
        amount_files_in_source=(amount_files_in_source := 10),
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
    ) as virtual_backup_env:
        backup_env_configs = virtual_backup_env.create()

        patch_multiple_configs(
            RsyncCommand, {"nas.json": backup_env_configs.nas_config, "sync.json": backup_env_configs.sync_config}
        )
        command = RsyncCommand().compose(virtual_backup_env.sink, virtual_backup_env.source)
        Popen(" ".join(command), shell=True).wait()
        assert len(list(virtual_backup_env.sink.iterdir())) == amount_files_in_source
        for file in virtual_backup_env.sink.iterdir():
            assert file.stat().st_size == 1024
