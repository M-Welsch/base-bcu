import os, sys
from time import sleep

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(path_to_module)
sys.path.append(path_to_module)

from base.common.config import Config
from base.backup.backup import BackupManager, BackupBrowser


if __name__ == '__main__':
    config = Config("/home/base/base/config.json")
    BM = BackupManager(config.config_backup)
    BM.backup()

    print("testing backup_finder")
    with BackupBrowser(config.config_backup) as bl:
        oldest_backup = bl.get_oldest_backup()
        print(f"oldest_backup = {oldest_backup}")
    sleep(10)  # give the logger some time ...