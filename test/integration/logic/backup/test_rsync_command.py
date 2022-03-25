from subprocess import PIPE, Popen
from test.utils.backup_environment.virtual_backup_environment import BackupTestEnvironment, BackupTestEnvironmentInput
from test.utils.patch_config import patch_multiple_configs

import pytest

from base.logic.backup.protocol import Protocol
from base.logic.backup.synchronisation.rsync_command import RsyncCommand


@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.SMB])
def test_composition(protocol: Protocol) -> None:
    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=protocol,
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
    )
    with BackupTestEnvironment(backup_environment_configuration) as virtual_backup_env:
        backup_env_configs = virtual_backup_env.create()

        patch_multiple_configs(
            RsyncCommand, {"nas.json": backup_env_configs.nas_config, "sync.json": backup_env_configs.sync_config}
        )
        command = RsyncCommand().compose(virtual_backup_env.sink, virtual_backup_env.source)
        Popen(command, shell=True).wait()
        for source_file, sink_file in zip(
            list(virtual_backup_env.source.iterdir()), list(virtual_backup_env.sink.iterdir())
        ):
            source_file_stat, sink_file_stat = source_file.stat(), sink_file.stat()
            assert source_file_stat.st_mode == sink_file_stat.st_mode
            assert source_file_stat.st_uid == sink_file_stat.st_uid
            assert source_file_stat.st_gid == sink_file_stat.st_gid
            assert source_file_stat.st_size == sink_file_stat.st_size
