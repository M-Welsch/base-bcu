import os, sys

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(path_to_module)
sys.path.append(path_to_module)

from base.common.config import Config
from base.common.nas_finder import NasFinder

if __name__ == '__main__':
    config = Config("/home/base/base/config.json")
    NF = NasFinder(config.config_backup)
    nas_ip = config.config_backup["ssh_host"]
    nas_user = config.config_backup["ssh_user"]
    print(NF._nas_hdd_mounted(nas_ip, nas_user))
    wrong_ip = '192.168.1.1'
    print(NF._nas_hdd_mounted(wrong_ip, nas_user))