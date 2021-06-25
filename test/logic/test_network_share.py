import shutil
import json
from pathlib import Path

import pytest

from base.logic.network_share import NetworkShare
from base.common.config import Config
from base.logic.nas import Nas


def update_conf(file_path, updates):
    with open(file_path, "r") as src:
        obj = json.load(src)
    obj.update(updates)
    with open(file_path, "w") as dst:
        json.dump(obj, dst)


@pytest.fixture(scope="class")
def network_share(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    Config.set_config_base_path(config_dir)
    yield NetworkShare()


class TestNetworkShare:
    @staticmethod
    def test_mount_datasource_via_smb(network_share):
        nas = Nas()
        nas.smb_backup_mode()
        network_share.mount_datasource_via_smb()
        assert nas.correct_smb_conf("backupmode")

    @staticmethod
    def test_unmount_datasource_via_smb(network_share):
        nas = Nas()
        nas.smb_normal_mode()
        network_share.unmount_datasource_via_smb()
        assert nas.correct_smb_conf("normalmode")
