import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Generator

import _pytest.tmpdir
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
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.schedule import Schedule


def update_conf(file_path: Path, updates: Dict[str, Any]) -> None:
    with open(file_path, "r") as src:
        obj = json.load(src)
    obj.update(updates)
    with open(file_path, "w") as dst:
        json.dump(obj, dst)


def make_base_application() -> BaSeApplication:
    base_app: BaSeApplication = BaSeApplication.__new__(BaSeApplication)
    base_app._config = Config("base.json")
    # base_app._setup_logger() # don't use it here! Otherwise everything will be logged twice.
    base_app._maintenance_mode = MaintenanceMode()
    base_app._backup_browser = BackupBrowser()
    base_app._hardware = Hardware(base_app._backup_browser)
    base_app._backup = Backup(base_app._maintenance_mode.is_on, backup_browser=base_app._backup_browser)
    base_app._schedule = Schedule()
    base_app._maintenance_mode.set_connections(
        [(base_app._schedule.backup_request, base_app._backup.on_backup_request)]
    )
    base_app._shutting_down = False
    base_app._connect_signals()
    return base_app


@pytest.fixture()
def app_smb(tmpdir_factory: _pytest.tmpdir.TempdirFactory) -> Generator[BaSeApplication, None, None]:
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    # update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(config_dir / "sync.json", {"remote_backup_source_location": "/mnt/HDD/testfiles", "protocol": "smb"})
    update_conf(config_dir / "backup.json", {"shutdown_between_backups": False})
    Config.set_config_base_path(config_dir)
    yield make_base_application()


@pytest.fixture()
def app_ssh(tmpdir_factory: _pytest.tmpdir.TempdirFactory) -> Generator[BaSeApplication, None, None]:
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    # update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(config_dir / "sync.json", {"remote_backup_source_location": "/mnt/HDD/testfiles", "protocol": "ssh"})
    update_conf(config_dir / "backup.json", {"shutdown_between_backups": False})
    Config.set_config_base_path(config_dir)
    yield make_base_application()


# @pytest.mark.skip
def test_backup_chain_via_smb(app_smb: BaSeApplication) -> None:
    app_smb._backup.on_backup_request()
    if app_smb._backup._sync is not None:
        app_smb._backup._sync.join()


# Todo: find a way to wait for last test to complete! Use backup_running request or so ...
# @pytest.mark.skip("find a way to wait for last test to complete! Use backup_running request or so ...")
def test_backup_chain_via_ssh(app_ssh: BaSeApplication) -> None:
    app_ssh._backup.on_backup_request()
