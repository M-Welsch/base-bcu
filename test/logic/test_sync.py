from datetime import datetime
import json
import sys
import os
import shutil
from pathlib import Path

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


@pytest.fixture(scope="class")
def sync(tmpdir_factory, configure_logger):
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir)/"config").resolve()
    general_backup_target_location = tmpdir_factory.mktemp(f"backup_target_location")
    backup_source_location = tmpdir_factory.mktemp(f"backup_source_location")
    shutil.copytree('/home/base/python.base/base/config', config_dir)
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    backup_target_location = (Path(general_backup_target_location)/f"backup_{timestamp}")
    shutil.copytree('/home/base/python.base/test/dummy_files', backup_source_location, dirs_exist_ok=True)
    update_conf(
        config_dir/"base.json",
        {"logs_directory": configure_logger["tmpdir"]}
    )
    update_conf(
        config_dir/"sync.json",
        {
            "remote_backup_source_location": str(backup_target_location),
            "protocol": "smb"
        }
    )
    update_conf(
        config_dir/"backup.json",
        {
            "shutdown_between_backups": False
        }
    )
    Config.set_config_base_path(config_dir)
    yield RsyncWrapperThread(backup_target_location, backup_source_location)


class TestSync:
    @staticmethod
    def test_sync(sync):
        sync.start()
