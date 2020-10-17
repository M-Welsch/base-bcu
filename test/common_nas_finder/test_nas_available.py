import os, sys

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(path_to_module)
sys.path.append(path_to_module)

from base.common.config import Config
from base.common.base_logging import Logger
from base.common.nas_finder import NasFinder

if __name__ == '__main__':
    config = Config("/home/base/base/config.json")
    logger = Logger('.')
    NF = NasFinder(logger)
    nas_ip = '192.168.0.100'
    print(NF.nas_avaliable(nas_ip))
    wrong_ip = '192.168.1.1'
    print(NF.nas_avaliable(wrong_ip))
    logger.terminate()