import os, sys

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

if __name__ == "__main__":
    from base.common.config import Config

    _config = Config("/home/maxi/base/config.json")
    _hardware_control = HWCTRL.global_instance(_config.config_hwctrl)
    _hardware_control.set_attiny_serial_path_to_communication()
    _hardware_control.enable_receiving_messages_from_attiny()