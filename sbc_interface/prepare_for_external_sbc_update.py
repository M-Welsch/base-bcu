import os, sys
from time import sleep
path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

if __name__ == "__main__":
    from base.hwctrl.hw_definitions import *
    pin = PinInterface(1)
    pin.set_attiny_serial_path_to_communication()
    pin.enable_receiving_messages_from_attiny()
    while True:
        sleep(1)
    pin.cleanup()
