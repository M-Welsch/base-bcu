from pathlib import Path

from base.common.config import get_config
from base.common.ssh_interface import SSHInterface


class Nas:
    def __init__(self) -> None:
        self._config = get_config("nas.json")

    def root_of_share(self, file: Path) -> Path:
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            return self._obtain_root_of_share(file, sshi)

    @staticmethod
    def _obtain_root_of_share(file: Path, sshi: SSHInterface) -> Path:
        response = sshi.run_and_raise(f'findmnt -T {file} --output="TARGET" -nf')
        return Path(response.strip())
