import sys
import os
import shutil
import json
from pathlib import Path

import pytest

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# TODO: Fix this somehow...
# print(path_to_module)
# print(os.getcwd())
# print('\n'.join(sys.path))
sys.path.append(path_to_module)

from base.base_application import BaSeApplication, MaintenanceMode
from base.common.config import Config
from base.hardware.hardware import Hardware
from base.logic.backup.backup import Backup
from base.logic.schedule import Schedule


def update_conf(file_path, updates):
    with open(file_path, "r") as src:
        obj = json.load(src)
    obj.update(updates)
    with open(file_path, "w") as dst:
        json.dump(obj, dst)


def make_base_application():
    base_app = BaSeApplication.__new__(BaSeApplication)
    base_app._config: Config = Config("base.json")
    # base_app._setup_logger() # don't use it here! Otherwise everything will be logged twice.
    base_app._maintenance_mode = MaintenanceMode()
    base_app._hardware = Hardware()
    base_app._backup = Backup(base_app._maintenance_mode.is_on)
    base_app._schedule = Schedule()
    base_app._maintenance_mode.set_connections(
        [(base_app._schedule.backup_request, base_app._backup.on_backup_request)]
    )
    base_app._shutting_down = False
    base_app._connect_signals()
    return base_app


@pytest.fixture()
def app_smb(tmpdir_factory, configure_logger):
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(config_dir / "sync.json", {"remote_backup_source_location": "/mnt/HDD/testfiles", "protocol": "smb"})
    update_conf(config_dir / "backup.json", {"shutdown_between_backups": False})
    Config.set_config_base_path(config_dir)
    yield make_base_application()


@pytest.fixture()
def app_ssh(tmpdir_factory, configure_logger):
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(config_dir / "sync.json", {"remote_backup_source_location": "/mnt/HDD/testfiles", "protocol": "ssh"})
    update_conf(config_dir / "backup.json", {"shutdown_between_backups": False})
    Config.set_config_base_path(config_dir)
    yield make_base_application()


# @pytest.mark.skip
def test_backup_chain_via_smb(app_smb):
    app_smb._backup.on_backup_request()
    app_smb._backup._sync.join()


# Todo: find a way to wait for last test to complete! Use backup_running request or so ...
# @pytest.mark.skip("find a way to wait for last test to complete! Use backup_running request or so ...")
def test_backup_chain_via_ssh(app_ssh):
    app_ssh._backup.on_backup_request()
