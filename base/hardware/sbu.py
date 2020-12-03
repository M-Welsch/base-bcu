from base.hardware.pin_interface import PinInterface
from base.common.config import Config


class SBU:
    def __init__(self):
        self._config = Config("/home/base/python.base/base/config/sbu.json")
        self._pin_interface = PinInterface.global_instance()





"""
Kommandoschicht
- write to display
- set display brightness
- set led brightness
--------------------------
- set next backup time
- set readable backup timestamp
--------------------------
- measure current
- measure vcc3v
- measure temperature
--------------------------
- request shutdown
- terminate serial connection


Protokollschicht
"""