import os, sys, glob, serial

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

if __name__ == "__main__":
    from base.common.config import Config
    from base.common.base_logging import Logger
    from base.hwctrl.hwctrl import *

    _config = Config("/home/maxi/base/config.json")
    _logger = Logger("/home/maxi/base/log")
    _hardware_control = HWCTRL(_config.config_hwctrl, _logger)
    _hardware_control.set_attiny_serial_path_to_communication()
    _hardware_control.enable_receiving_messages_from_attiny()