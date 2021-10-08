import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Any, Generator

import _pytest
import pytest

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)

from base.common.config import Config
from base.logic.backup.sync import RsyncWrapperThread


def update_conf(file_path: Path, updates: Any) -> None:
    with open(file_path, "r") as src:
        obj = json.load(src)
    obj.update(updates)
    with open(file_path, "w") as dst:
        json.dump(obj, dst)


@pytest.fixture
def sync_ssh(tmpdir_factory: _pytest.tmpdir.TempdirFactory) -> Generator[RsyncWrapperThread, None, None]:
    backup_source_location = Path(tmpdir_factory.mktemp("backup_source_location"))
    backup_target_location = Path(tmpdir_factory.mktemp("backup_target_location"))
    rsync_wrapper_thread = RsyncWrapperThread(backup_target_location, backup_source_location)
    raise ZeroDivisionError(f"y<<<<<<< {dir(rsync_wrapper_thread._ssh_rsync)}")
    rsync_wrapper_thread._ssh_rsync._nas_config["ssh_host"] = "localhost"
    rsync_wrapper_thread._ssh_rsync._nas_config["ssh_user"] = "base"
    rsync_wrapper_thread._ssh_rsync._sync_config["protocol"] = "ssh"
    rsync_wrapper_thread._ssh_rsync._sync_config["ssh_keyfile_path"] = "/home/base/.ssh/id_rsa"
    yield rsync_wrapper_thread
    # Fixme: AttributeError: 'SshRsync' object has no attribute '_nas_config'


@pytest.fixture
def sync_smb(tmpdir_factory: _pytest.tmpdir.TempdirFactory) -> Generator[RsyncWrapperThread, None, None]:
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    general_backup_target_location = tmpdir_factory.mktemp(f"backup_target_location")
    backup_source_location = Path(tmpdir_factory.mktemp(f"backup_source_location"))
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    backup_target_location = Path(general_backup_target_location) / f"backup_{timestamp}"
    shutil.copytree("/home/base/python.base/test/dummy_files", str(backup_source_location), dirs_exist_ok=True)
    # TODO: Maybe collect logfiles from tests in single directory in the future. Via autouse fixture?
    # update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(
        config_dir / "sync.json", {"remote_backup_source_location": str(backup_target_location), "protocol": "smb"}
    )
    update_conf(config_dir / "backup.json", {"shutdown_between_backups": False})
    Config.set_config_base_path(config_dir)
    yield RsyncWrapperThread(backup_target_location, backup_source_location)


@pytest.fixture
def sync_ssh_(tmpdir_factory: _pytest.tmpdir.TempdirFactory) -> Generator[RsyncWrapperThread, None, None]:
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    general_backup_target_location = tmpdir_factory.mktemp(f"backup_target_location")
    backup_source_location = Path(tmpdir_factory.mktemp(f"backup_source_location"))
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    backup_target_location = Path(general_backup_target_location) / f"backup_{timestamp}"
    shutil.copytree("/home/base/python.base/test/dummy_files", str(backup_source_location), dirs_exist_ok=True)
    # TODO: Maybe collect logfiles from tests in single directory in the future. Via autouse fixture?
    # update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(
        config_dir / "sync.json", {"remote_backup_source_location": str(backup_target_location), "protocol": "ssh"}
    )
    update_conf(config_dir / "backup.json", {"shutdown_between_backups": False})
    update_conf(config_dir / "nas.json", {"ssh_host": "192.168.0.61", "ssh_user": "base"})
    Config.set_config_base_path(config_dir)
    yield RsyncWrapperThread(backup_target_location, backup_source_location)


@pytest.mark.skip
def test_sync_smb(sync_smb: RsyncWrapperThread) -> None:
    sync_smb.start()
    sleep(2)


def test_sync_ssh(sync_ssh: RsyncWrapperThread) -> None:
    print(
        "for this test to work you have to enable ssh access to yourself by "
        "'sudo ssh-copy-id -i ~/.ssh/id_rsa.pub base@192.168.0.61'. Replace the ip-address with your BaSe's."
        "The 'sudo' is important."
    )
    sync_ssh.start()
