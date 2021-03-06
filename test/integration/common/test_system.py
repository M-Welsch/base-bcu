from getpass import getuser
from pathlib import Path
from subprocess import PIPE, Popen
from test.utils.backup_environment.virtual_backup_environment import (  # fixture, don't remove
    prepare_source_sink_dirs,
    temp_source_sink_dirs,
)
from test.utils.patch_config import patch_multiple_configs
from typing import Dict, Tuple

import pytest

from base.common.system import System
from base.logic.backup.synchronisation.rsync_command import RsyncCommand


def test_obtain_size_of_next_backup_increment_smb(temp_source_sink_dirs: Tuple[Path, Path]) -> None:
    patch_multiple_configs(RsyncCommand, {"sync.json": {"protocol": "smb"}, "nas.json": {}})
    src, sink = temp_source_sink_dirs
    bytesize_of_each_file = 1024
    amount_files_in_src = 2
    amount_preexisting_files_in_sink = 1
    prepare_source_sink_dirs(src, sink, amount_files_in_src, bytesize_of_each_file, amount_preexisting_files_in_sink)
    size_of_next_increment = System.size_of_next_backup(source_location=Path(src), local_target_location=Path(sink))
    assert size_of_next_increment == bytesize_of_each_file * (amount_files_in_src - amount_preexisting_files_in_sink)


def test_obtain_size_of_next_backup_increment_ssh(temp_source_sink_dirs: Tuple[Path, Path]) -> None:
    user = getuser()
    patch_multiple_configs(
        RsyncCommand,
        {
            "sync.json": {"ssh_keyfile_path": f"/home/{user}/.ssh/id_rsa", "protocol": "ssh"},
            "nas.json": {"ssh_host": "127.0.0.1", "ssh_user": user},
        },
    )
    src, sink = temp_source_sink_dirs
    bytesize_of_each_file = 1024
    amount_files_in_src = 2
    amount_preexisting_files_in_sink = 1
    prepare_source_sink_dirs(src, sink, amount_files_in_src, bytesize_of_each_file, amount_preexisting_files_in_sink)
    size_of_next_increment = System.size_of_next_backup(source_location=Path(src), local_target_location=Path(sink))
    try:
        assert size_of_next_increment == bytesize_of_each_file * (
            amount_files_in_src - amount_preexisting_files_in_sink
        )
    except AssertionError as e:
        print(
            f"""!!! This test needs preparation !!!
Make sure the following applies to your machine:
- rsync is installed
- you ran 'ssh-copy-id -i ~/.ssh/id_rsa.pub {user}>@127.0.0.1'
  - you can test this by running 'ssh {user}@127.0.0.1' You shouldn't be asked for password and see your own commandline afterwards
"""
        )
        raise e


def test_get_bytesize_of_directories(temp_source_sink_dirs: Tuple[Path, Path]) -> None:
    src, sink = temp_source_sink_dirs
    bytesize_of_each_file = 1024
    amount_files_in_src = 2
    prepare_source_sink_dirs(src, sink, amount_files_in_src, bytesize_of_each_file)
    sizes = get_bytesize_of_directories(src.parent)
    size_overhead_by_directory_structure = 4096
    assert all([isinstance(key, Path) and isinstance(value, int) for key, value in sizes.items()])
    assert sizes[src] == size_overhead_by_directory_structure + bytesize_of_each_file * amount_files_in_src


@pytest.mark.parametrize("amount_preexisting_files_in_sink", [0, 1, 2])
def test_cp_newst_bu_hardlinks(temp_source_sink_dirs: Tuple[Path, Path], amount_preexisting_files_in_sink: int) -> None:
    src, sink = temp_source_sink_dirs
    bytesize_of_each_file = 1024
    amount_files_in_src = 2
    prepare_source_sink_dirs(src, sink, amount_files_in_src, bytesize_of_each_file, amount_preexisting_files_in_sink)
    System.copy_newest_backup_with_hardlinks(recent_backup=src, new_backup=sink)
    size_overhead_by_directory_struct = 4096
    sizes = get_bytesize_of_directories(src.parent)
    assert sizes[src] == size_overhead_by_directory_struct + amount_files_in_src * bytesize_of_each_file
    assert sizes[sink] == size_overhead_by_directory_struct + amount_preexisting_files_in_sink * bytesize_of_each_file


def get_bytesize_of_directories(directory: Path) -> Dict[Path, int]:
    # this function is not used in the production code, but necessary for testing.
    # It has some complexity and therefore has to be tested like any function production code.
    command = f"du -b {directory.absolute()}"
    print(f"size obtain command: {command}")
    p = Popen(command.split(), stdout=PIPE, stderr=PIPE)
    sizes = {}
    if p.stdout is not None:
        for line in p.stdout.readlines():
            size_of_current_dir, current_dir = line.decode().strip().split("\t")
            sizes[Path(current_dir)] = int(size_of_current_dir)
    return sizes
