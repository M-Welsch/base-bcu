import pytest

from base.logic.network_share import NetworkShare


@pytest.fixture
def network_share():
    yield NetworkShare()


def test_mount_datasource_via_smb(network_share):
    network_share.mount_datasource_via_smb()