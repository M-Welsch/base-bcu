import os, sys
from time import sleep

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(path_to_module)
sys.path.append(path_to_module)

from base.common.config import Config
from base.common.base_logging import Logger
from base.backup.backup import BackupManager, BackupLister

if __name__ == '__main__':
    config = Config("/home/base/base/config.json")
    logger = Logger('.')
    BM = BackupManager(config.backup_config, logger)
    BM.backup()

    print("testing backup_finder")
    with BackupLister(config.backup_config) as bl:
        oldest_backup = bl.get_oldest_backup()
        print(f"oldest_backup = {oldest_backup}")
    sleep(0.1) # give the logger some time ...
    logger.terminate()