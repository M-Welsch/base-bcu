# background:
# the following command usually returns "/".
# However there might be cases where this doesn't hold true
# findmnt -T /home/$(whoami) --output="TARGET" -nf
from getpass import getuser
from pathlib import Path
from subprocess import PIPE, Popen
from test.utils import patch_config

from base.logic.nas import Nas


def test_root_of_share() -> None:
    def mount_target_of_homedir(user: str) -> Path:
        p = Popen(f'findmnt -T /home/{user} --output="TARGET" -nf', shell=True, stdout=PIPE)
        return Path(p.stdout.readlines()[-1].decode().strip())  # type: ignore

    user = getuser()
    patch_config(Nas, {"ssh_host": "127.0.0.1", "ssh_user": user})
    mount_target = Nas().root_of_share(Path(f"/home/{user}"))
    assert mount_target == mount_target_of_homedir(user)
    assert isinstance(mount_target, Path)
