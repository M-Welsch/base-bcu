import json
from pathlib import Path
import os

import pytest

from base.logic.backup.backup import Backup
from base.common.config import Config
from base.common.exceptions import NasNotMountedError, BackupRequestError


def false():
    return False


@pytest.fixture()
def backup(tmpdir):
    config_path = Path("/home/base/python.base/base/config/")
    config_test_path = Path(tmpdir.mkdir("config"))
    source = tmpdir.mkdir("source")
    file = source.join("xyz.txt")
    file.write("Test")
    target = tmpdir.mkdir("target")
    with open(config_path/"sync.json", "r") as src, open(config_test_path/"sync.json", "w") as dst:
        sync_config_data = json.load(src)
        sync_config_data["remote_backup_source_location"] = str(source)
        sync_config_data["local_backup_target_location"] = str(target)
        json.dump(sync_config_data, dst)
    with open(config_path/"backup.json", "r") as src, open(config_test_path/"backup.json", "w") as dst:
        backup_config_data = json.load(src)
        json.dump(backup_config_data, dst)
    with open(config_path/"nas.json", "r") as src, open(config_test_path/"nas.json", "w") as dst:
        nas_config_data = json.load(src)
        json.dump(nas_config_data, dst)
    Config.set_config_base_path(config_test_path)
    yield Backup(false)
    print("source contents:", os.listdir(str(source)))
    print("target contents:", os.listdir(str(target)))


def test_backup(backup):
    backup.on_backup_request()
