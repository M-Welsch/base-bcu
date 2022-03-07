from pathlib import Path
from typing import List

from base.common.config import get_config
from base.common.logger import LoggerFactory
from base.common.ssh_interface import SSHInterface

LOG = LoggerFactory.get_logger(__name__)


class Nas:
    def __init__(self) -> None:
        self._config = get_config("nas.json")

    def root_of_share(self, file: Path) -> Path:
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            response = sshi.run_and_raise(f'findmnt -T {file} --output="TARGET" -nf')
            response = response.strip()
            return Path(response)
