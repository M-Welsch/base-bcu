import logging
import sys
from pathlib import Path

import pytest

from base.logic.backup import Backup, BackupRequestError
from base.common.config import Config


@pytest.fixture(autouse=True)
def configure_logger():
    # Path(self._config.logs_directory).mkdir(exist_ok=True)
    logging.basicConfig(
        # filename=Path(self._config.logs_directory)/datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log'),
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(name)s: %(message)s',
        datefmt='%m.%d.%Y %H:%M:%S'
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


@pytest.fixture()
def backup():
    config_path = Path("/home/base/python.base/base/config/")
    Config.set_config_base_path(config_path)
    yield Backup()


def test_check_for_running_backup(backup):
    backup._sync.start()
    with pytest.raises(BackupRequestError) as e:
        backup.check_for_running_backup()
    backup._sync.terminate()
