import os, sys

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(path_to_module)
sys.path.append(path_to_module)

from base.common.config import Config
from base.common.base_logging import Logger
from base.backup.backup import BackupManager

if __name__ == '__main__':
    config = Config("/home/base/base/config.json")
    logger = Logger('.')
    BM = BackupManager(config.backup_config, logger)
    BM.backup()