import json
import shutil
from pathlib import Path
from subprocess import PIPE, Popen, call
from typing import Any, Dict, Generator, Union

import _pytest
import pytest

from base.common.config import BoundConfig
from base.common.exceptions import NetworkError
from base.logic.nas import Nas
from base.logic.network_share import NetworkShare


def update_conf(file_path: Path, updates: Any) -> None:
    with open(file_path, "r") as src:
        obj = json.load(src)
    obj.update(updates)
    with open(file_path, "w") as dst:
        json.dump(obj, dst)


@pytest.fixture(scope="class")
def network_share(tmpdir_factory: _pytest.tmpdir.TempdirFactory) -> Generator[NetworkShare, None, None]:
    tmpdir = tmpdir_factory.mktemp("test_dir")
    config_dir = (Path(tmpdir) / "config").resolve()
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    BoundConfig.set_config_base_path(config_dir)
    yield NetworkShare()


@pytest.fixture()
def virtual_network_share(
    tmpdir_factory: pytest.TempdirFactory,
) -> Generator[Dict[str, Union[NetworkShare, Path]], None, None]:
    dirs = {
        "smb_datasource": tmpdir_factory.mktemp("smb_datasource"),
        "vanilla_smb_conf": Path(__file__).parent / "smb.conf",
        "modified_smb_conf": Path(__file__).parent / "smb.conf_mod",
        "credentials_file": Path(__file__).parent / "credentials",
    }
    setup_smb_share(dirs)

    # Mock Config
    config_dir = (Path(dirs["smb_datasource"]) / "config").resolve()
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    nas_config = config_dir / "nas.json"
    update_conf(
        nas_config, {"smb_host": "127.0.0.1", "smb_user": "base", "smb_credentials_file": str(dirs["credentials_file"])}
    )
    BoundConfig.set_config_base_path(config_dir)
    yield {"nws": NetworkShare(), "nas_cfg": nas_config}
    teardown_smb_share(dirs)


def setup_smb_share(dirs: dict) -> None:
    call("sudo mv /etc/samba/smb.conf /etc/samba/smb.conf_bu".split(), stderr=PIPE, stdout=PIPE)
    shutil.copy(dirs["vanilla_smb_conf"], dirs["modified_smb_conf"])
    with open(dirs["modified_smb_conf"], "a") as smb_conf:
        smb_conf.write("\n\n[hdd]\n")
        smb_conf.write("  browsable = yes\n")
        smb_conf.write(f'  path = {dirs["smb_datasource"]}\n')
        smb_conf.write(f"  guest ok = yes\n")
    call(f'sudo cp {dirs["modified_smb_conf"]} /etc/samba/smb.conf'.split(), stderr=PIPE, stdout=PIPE)
    restart_smbd()
    with open(dirs["credentials_file"], "w") as cred_file:
        cred_file.write("user=nobody\n")
        cred_file.write("password=\n")
        cred_file.write("domain=WORKGROUP")
    assert Path("/etc/samba/smb.conf").is_file()
    assert Path("/etc/samba/smb.conf_bu").is_file()
    assert dirs["credentials_file"].is_file()


def teardown_smb_share(dirs: dict) -> None:
    call("sudo mv /etc/samba/smb.conf_bu /etc/samba/smb.conf".split(), stderr=PIPE, stdout=PIPE)
    restart_smbd()
    dirs["modified_smb_conf"].unlink()
    dirs["credentials_file"].unlink()
    assert not dirs["modified_smb_conf"].is_file()
    assert not Path("/etc/samba/smb.conf_bu").is_file()
    assert not dirs["credentials_file"].is_file()


def restart_smbd() -> None:
    call("sudo systemctl restart smbd".split(), stderr=PIPE, stdout=PIPE)


def check_share_mounted(share_name: str) -> bool:
    p = Popen(f"mount | grep {share_name}", shell=True, stdout=PIPE)
    if p.stdout is not None:
        return share_name in str(p.stdout.read())
    else:
        return False


class TestNetworkShare:
    def test_mount_datasource(self, virtual_network_share: dict) -> None:
        network_share: NetworkShare = virtual_network_share["nws"]
        network_share.mount_datasource_via_smb()
        assert check_share_mounted(network_share._config.local_nas_hdd_mount_point)
        network_share.unmount_datasource_via_smb()
        assert not check_share_mounted(network_share._config.local_nas_hdd_mount_point)

    def test_mount_datasource_already_mounted(self, virtual_network_share: dict) -> None:
        network_share: NetworkShare = virtual_network_share["nws"]
        network_share.mount_datasource_via_smb()
        assert check_share_mounted(network_share._config.local_nas_hdd_mount_point)
        network_share.mount_datasource_via_smb()
        # Todo: check whether line "Device probably already mounted" appears in logfile
        network_share.unmount_datasource_via_smb()
        assert not check_share_mounted(network_share._config.local_nas_hdd_mount_point)

    def test_mount_unavailable_datasource(self, virtual_network_share: dict) -> None:
        network_share: NetworkShare = virtual_network_share["nws"]
        nas_cfg = virtual_network_share["nas_cfg"]
        orig_smb_share_name = BoundConfig(nas_cfg).smb_share_name
        update_conf(nas_cfg, {"smb_share_name": "invalid"})
        with pytest.raises(NetworkError):
            network_share.mount_datasource_via_smb()
        update_conf(nas_cfg, {"smb_share_name": orig_smb_share_name})

    def test_mount_corrupt_ip_address(self, virtual_network_share: dict) -> None:
        network_share: NetworkShare = virtual_network_share["nws"]
        nas_cfg = virtual_network_share["nas_cfg"]
        orig_smb_host = BoundConfig(nas_cfg).smb_host
        update_conf(nas_cfg, {"smb_host": "1922.1688.0.1000"})
        with pytest.raises(NetworkError):
            network_share.mount_datasource_via_smb()
        update_conf(nas_cfg, {"smb_host": orig_smb_host})
