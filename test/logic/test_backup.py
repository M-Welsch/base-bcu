import json
import logging
import sys
from pathlib import Path
import os

import pytest

from base.logic.backup import Backup, BackupRequestError
from base.common.config import Config


@pytest.fixture(autouse=True)
def configure_logger():
    # Path(self._config.logs_directory).mkdir(exist_ok=True)
    logging.basicConfig(
        # filename=Path(self._config.logs_directory)/datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log'),
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(name)s: %(message)s',
        datefmt='%m.%d.%Y %H:%M:%S'
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


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
    backup.check_for_source_hdd_readiness()


def test_ask_weather_frog_for_permission(backup):
    backup.ask_weather_frog_for_permission()


@pytest.mark.skip
def test_check_for_hardware_readiness(backup):
    backup.check_for_hardware_readiness()


@pytest.mark.skip
def test_check_for_drive_readiness(backup):
    backup.check_for_drive_readiness()
