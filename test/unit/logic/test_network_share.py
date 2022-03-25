import logging
import subprocess
from subprocess import PIPE, Popen
from test.utils.patch_config import patch_config
from typing import Generator, Optional, Type

import pytest
from _pytest.logging import LogCaptureFixture

from base.common.exceptions import NetworkError
from base.logic.network_share import NetworkShare


@pytest.fixture(scope="class")
def network_share() -> Generator[NetworkShare, None, None]:
    patch_config(NetworkShare, {"smb_host": "127.0.0.1", "smb_user": "base"})
    yield NetworkShare()
