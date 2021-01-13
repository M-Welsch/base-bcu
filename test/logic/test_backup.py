import json
from pathlib import Path
import os

import pytest

from base.logic.backup import Backup
from base.common.config import Config
from base.common.exceptions import NasNotMountedError, BackupRequestError


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
    with open(config_path/"backup.json", "r") as src, open(config_test_path/"backup.json","w") as dst:
        backup_config_data = json.load(src)
        json.dump(backup_config_data, dst)
    Config.set_config_base_path(config_test_path)
    yield Backup()
    print("source contents:", os.listdir(str(source)))
    print("target contents:", os.listdir(str(target)))


def test_check_for_running_backup(backup):
    backup.check_for_running_backup()
    # backup._sync.start()
    # with pytest.raises(BackupRequestError) as e:
    #     backup.check_for_running_backup()
    # backup._sync.terminate()


def test_check_for_maintenance_mode(backup):
    backup.check_for_maintenance_mode()


def test_check_for_network_reachability(backup):
    backup.check_for_network_reachability()


@pytest.mark.slow
def test_check_for_source_device_reachability(backup):
    backup.check_for_source_device_reachability()


def test_check_for_source_hdd_readiness(backup):
    # check_for_source_hdd_readiness() check whether the NAS-HDD
    # is mounted on a path specified in the config file
    # however for these tests, this key in the config file is overwritten
    # by a temporary location. This is why this test will fail
    with pytest.raises((NasNotMountedError, BackupRequestError)):
        backup.check_for_source_hdd_readiness()


def test_ask_weather_frog_for_permission(backup):
    backup.ask_weather_frog_for_permission()


@pytest.mark.skip
def test_check_for_hardware_readiness(backup):
    backup.check_for_hardware_readiness()


@pytest.mark.skip
def test_check_for_drive_readiness(backup):
    backup.check_for_drive_readiness()
