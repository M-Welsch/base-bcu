import pytest
import json
from pathlib import Path

from base.common.config import Config
from base.logic.nas import Nas


@pytest.fixture(scope="class")
def nas(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("nas_test_config_dir")
    config_path = Path("/home/base/python.base/base/config/")
    config_test_path = Path(tmpdir.mkdir("config"))
    with open(config_path / "nas.json", "r") as src, open(config_test_path / "nas.json", "w") as dst:
        sync_config_data = json.load(src)
        sync_config_data["services"].append("nonexistent_test_service")
        json.dump(sync_config_data, dst)
    with open(config_path / "sync.json", "r") as src, open(config_test_path / "sync.json", "w") as dst:
        sync_config_data = json.load(src)
        sync_config_data["protocol"] = "sftp"
        json.dump(sync_config_data, dst)
    Config.set_config_base_path(config_test_path)
    yield Nas()


class TestNas:
    @staticmethod
    def test_smb_backup_mode(nas):
        nas.smb_backup_mode()

    @staticmethod
    def test_smb_normal_mode(nas):
        nas.smb_normal_mode()

    @staticmethod
    def test_stopping_services(nas):
        nas.stop_services()

    @staticmethod
    def test_resume_services(nas):
        nas.resume_services()

    @staticmethod
    def test_correct_smb_conf(nas):
        assert nas.correct_smb_conf()
