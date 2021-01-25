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

from base.base_application import BaSeApplication
from base.common.config import Config


def update_conf(file_path, updates):
    with open(file_path, "r") as src:
        obj = json.load(src)
    obj.update(updates)
    with open(file_path, "w") as dst:
        json.dump(obj, dst)


@pytest.fixture()
def app(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = Path(tmpdir+"/config")
    shutil.copytree('/home/base/python.base/base/config', config_dir)
    update_conf(
        config_dir/"sync.json",
        {"ssh_host": "192.168.178.64", "remote_backup_source_location": "/home/maximilian/testfiles"}
    )
    Config.set_config_base_path(config_dir)
    yield BaSeApplication()


def test_backup_chain(app):
    app._backup.on_backup_request()
