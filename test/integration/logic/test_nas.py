# background:
# the following command usually returns "/".
# However there might be cases where this doesn't hold true
# findmnt -T /home/$(whoami) --output="TARGET" -nf
from getpass import getuser
from pathlib import Path
from subprocess import PIPE, Popen
from test.utils.patch_config import patch_config
from typing import Optional, Type

import pytest

from base.common.exceptions import NasSmbConfError
from base.logic.nas import Nas


@pytest.mark.parametrize("share_name, error", [("Backup", None), ("InvalidOne", NasSmbConfError)])
def test_root_of_share(share_name: str, error: Optional[Type[NasSmbConfError]]) -> None:
    def function_under_test() -> Path:
        return Nas().root_of_share(share_name)

    user = getuser()
    patch_config(Nas, {"ssh_host": "127.0.0.1", "ssh_user": user})
    if error is not None:
        with pytest.raises(error):
            function_under_test()
    else:
        mount_target = function_under_test()
        assert mount_target == Path("/tmp/base_tmpshare")
        assert isinstance(mount_target, Path)
