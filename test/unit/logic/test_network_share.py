from test.utils.patch_config import patch_config
from typing import Generator

import pytest

from base.logic.network_share import NetworkShare


@pytest.fixture(scope="class")
def network_share() -> Generator[NetworkShare, None, None]:
    patch_config(NetworkShare, {"smb_host": "127.0.0.1", "smb_user": "base"})
    yield NetworkShare()
