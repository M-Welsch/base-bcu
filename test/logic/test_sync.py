import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from time import sleep

import pytest

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)

from base.common.config import Config
from base.logic.backup.sync import RsyncWrapperThread


def update_conf(file_path, updates):
    with open(file_path, "r") as src:
        obj = json.load(src)
    obj.update(updates)
    with open(file_path, "w") as dst:
        json.dump(obj, dst)


@pytest.fixture
def sync_smb(tmpdir_factory, configure_logger):
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    general_backup_target_location = tmpdir_factory.mktemp(f"backup_target_location")
    backup_source_location = tmpdir_factory.mktemp(f"backup_source_location")
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    backup_target_location = Path(general_backup_target_location) / f"backup_{timestamp}"
    shutil.copytree("/home/base/python.base/test/dummy_files", backup_source_location, dirs_exist_ok=True)
    update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(
        config_dir / "sync.json", {"remote_backup_source_location": str(backup_target_location), "protocol": "smb"}
    )
    update_conf(config_dir / "backup.json", {"shutdown_between_backups": False})
    Config.set_config_base_path(config_dir)
    yield RsyncWrapperThread(backup_target_location, backup_source_location)


@pytest.fixture
def sync_ssh(tmpdir_factory, configure_logger):
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    general_backup_target_location = tmpdir_factory.mktemp(f"backup_target_location")
    backup_source_location = tmpdir_factory.mktemp(f"backup_source_location")
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    backup_target_location = Path(general_backup_target_location) / f"backup_{timestamp}"
    shutil.copytree("/home/base/python.base/test/dummy_files", backup_source_location, dirs_exist_ok=True)
    update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(
        config_dir / "sync.json", {"remote_backup_source_location": str(backup_target_location), "protocol": "ssh"}
    )
    update_conf(config_dir / "backup.json", {"shutdown_between_backups": False})
    update_conf(config_dir / "nas.json", {"ssh_host": "192.168.0.61", "ssh_user": "base"})
    Config.set_config_base_path(config_dir)
    yield RsyncWrapperThread(backup_target_location, backup_source_location)


def test_sync_smb(sync_smb):
    sync_smb.start()
    sleep(2)


def test_sync_ssh(sync_ssh):
    print(
        "for this test to work you have to enable ssh access to yourself by "
        "'sudo ssh-copy-id -i ~/.ssh/id_rsa.pub base@192.168.0.61'. Replace the ip-address with yours."
        "The 'sudo' is important."
    )
    sync_ssh.start()
