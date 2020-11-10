# creen
# creenShots
# XcreenShots
# ScreenShots

import logging
from pathlib import Path
from threading import Thread

from base.hwctrl.hw_definitions import *
from base.hwctrl.dock_undock import *
from base.common.config import Config


log = logging.getLogger(Path(__file__).name)


class HWCTRL(Thread):
    __instance = None

    @staticmethod
    def global_instance():
        if HWCTRL.__instance is None:
            HWCTRL()
        return HWCTRL.__instance

    def __init__(self):
        super(HWCTRL, self).__init__()

        if HWCTRL.__instance is not None:
            raise Exception("This class is a singleton!")

        HWCTRL.__instance = self

        config = Config.global_instance()
        self._config = config.config_hwctrl
        self._status = {}

        self.cur_meas = Current_Measurement(1)

        self.exitflag = False

        self.maximum_docking_time = self._config["maximum_docking_time"]
        self.docking_overcurrent_limit = self._config["docking_overcurrent_limit"]

        self._pin_interface = PinInterface(self._config["display_default_brightness"])
        self._hw_rev = self.get_hw_revision()
        print(f"HWCTRL recognized HW {self._hw_rev}")
        self.dock_undock = DockUndock(self._pin_interface, self._config, self._hw_rev)

        self.HB = Heartbeat(self._pin_interface.set_heartbeat_high, self._pin_interface.set_heartbeat_low)
        self.HB.start()

    @property
    def pin_interface(self):
        return self._pin_interface

    def get_hw_revision(self):
        hw_rev = self._pin_interface.get_hw_revision()

        return hw_rev

    def run(self):
        while not self.exitflag:
            sleep(1)

    def terminate(self):
        print("HWCTRL shutting down")
        log.info("HWCTRL is shutting down. Current status: {}".format(self._status))
        self.exitflag = True
        self.disable_receiving_messages_from_attiny()
        self.HB.terminate()
        self._pin_interface.cleanup()
        if self.cur_meas.is_alive():
            self.cur_meas.terminate()

    def _button_0_pressed(self):
        button_0_pressed = False
        if self._hw_rev == 'rev2':
            # buttons are low-active on rev2!
            button_0_pressed = not self._pin_interface.button_0_pin_high
        elif self._hw_rev == 'rev3':
            # buttons are high-active on rev3 (thanks to sbc)
            button_0_pressed = self._pin_interface.button_0_pin_high

        if button_0_pressed:
            log.info("Button 0 pressed")
        return button_0_pressed

    def _button_1_pressed(self):
        button_1_pressed = False
        if self._hw_rev == 'rev2':
            # buttons are low-active!
            button_1_pressed = not self._pin_interface.button_1_pin_high
        elif self._hw_rev == 'rev3':
            # buttons are high-active on rev3 (thanks to sbc)
            button_1_pressed = self._pin_interface.button_1_pin_high

        if button_1_pressed:
            log.info("Button 1 pressed")
        return button_1_pressed

    def pressed_buttons(self):
        return self._button_0_pressed(), self._button_1_pressed()

    def docked(self):
        return not self._pin_interface.docked_sensor_pin_high

    def undocked(self):
        return not self._pin_interface.undocked_sensor_pin_high

    def dock(self):
        self.dock_undock.dock()

    def undock(self):
        self.dock_undock.undock()

    def hdd_power_on(self):
        log.info("Powering HDD")
        if self._hw_rev == 'rev2':
            self.cur_meas = Current_Measurement(1)
            self.cur_meas.start()
        self._pin_interface.activate_hdd_pin()

    def hdd_power_off(self):
        log.info("Unpowering HDD")
        self._pin_interface.deactivate_hdd_pin()
        if self._hw_rev == 'rev2':
            self.cur_meas.terminate()

    def dock_and_power(self):
        # self.dock()
        self.dock_undock.dock()
        self.hdd_power_on()

    def unpower_and_undock(self):
        self.hdd_power_off()
        sleep(5)
        self.undock()

    def set_attiny_serial_path_to_sbc_fw_update(self):
        self._pin_interface.set_attiny_serial_path_to_sbc_fw_update()

    def set_attiny_serial_path_to_communication(self):
        self._pin_interface.set_attiny_serial_path_to_communication()

    def enable_receiving_messages_from_attiny(self):
        log.info(
            "Enabling receiving Messages from SBC by setting signal EN_attiny_link = HIGH. WARNING! "
            "This signal has to be set LOW before BPi goes to sleep! "
            "Hazard of Current flowing in the Rx-Pin of the BPi and destroying it!"
        )
        self._pin_interface.enable_receiving_messages_from_attiny()

    def disable_receiving_messages_from_attiny(self):
        log.info("Disabling receiving Messages from SBC by setting signal EN_attiny_link = LOW")
        self._pin_interface.disable_receiving_messages_from_attiny()

    @pin_interface.setter
    def pin_interface(self, value):
        self._pin_interface = value


class Heartbeat(Thread):
    def __init__(self, fkt_heartbeat_high, fkt_heartbeat_low):
        super(Heartbeat, self).__init__()
        self._fkt_heartbeat_high = fkt_heartbeat_high
        self._fkt_heartbeat_low = fkt_heartbeat_low
        self._heartbeat_state = 0
        self._exitflag = False

    def run(self):
        while not self._exitflag:
            if self._heartbeat_state:
                self._heartbeat_state = 0
                self._fkt_heartbeat_low()
            else:
                self._fkt_heartbeat_high()
                self._heartbeat_state = 1
            sleep(0.01)

    def terminate(self):
        self._exitflag = True
