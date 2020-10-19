# creen
# creenShots
# XcreenShots
# ScreenShots

import json
import time
from threading import Thread, Timer, get_ident
from queue import Queue

from base.hwctrl.hw_definitions import *
from base.hwctrl.current_measurement import Current_Measurement
from base.hwctrl.dock_undock import *

class HWCTRL(Thread):
	def __init__(self, config, logger):
		super(HWCTRL, self).__init__()

		self._config = config
		self._status = {}
		self._logger = logger

		self.cur_meas = Current_Measurement(1)

		self.exitflag = False

		self.maximum_docking_time = self._config["maximum_docking_time"]
		self.docking_overcurrent_limit = self._config["docking_overcurrent_limit"]

		self._pin_interface = PinInterface(self._config["display_default_brightness"])
		self._hw_rev = self.get_hw_revision()
		print(f"HWCTRL recognized HW {self._hw_rev}")
		self.dock_undock = DockUndock(self._pin_interface, self._logger, self._config, self._hw_rev)
		self.start_heartbeat()

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
		self._logger.info("HWCTRL is shutting down. Current status: {}".format(self._status))
		self.exitflag = True
		self.disable_receiving_messages_from_attiny()
		self.HB.terminate()
		self._pin_interface.cleanup()
		if self.cur_meas.is_alive():
			self.cur_meas.terminate()

	def _button_0_pressed(self):
		if self._hw_rev == 'rev2':
			# buttons are low-active on rev2!
			button_0_pressed = not self._pin_interface.button_0_pin_high
		elif self._hw_rev == 'rev3':
			# buttons are high-active on rev3 (thanks to sbc)
			button_0_pressed = self._pin_interface.button_0_pin_high

		if button_0_pressed:
			self._logger.info("Button 0 pressed")
		return button_0_pressed

	def _button_1_pressed(self):
		if self._hw_rev == 'rev2':
			# buttons are low-active!
			button_1_pressed = not self._pin_interface.button_1_pin_high
		elif self._hw_rev == 'rev3':
			# buttons are high-active on rev3 (thanks to sbc)
			button_1_pressed =  self._pin_interface.button_1_pin_high

		if button_1_pressed:
			self._logger.info("Button 1 pressed")
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
		self._logger.info("Powering HDD")
		if self._hw_rev == 'rev2':
			self.cur_meas = Current_Measurement(1)
			self.cur_meas.start()
		self._pin_interface.activate_hdd_pin()

	def hdd_power_off(self):
		self._logger.info("Unpowering HDD")
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
		self._logger.info("Enabling receiving Messages from SBC by setting signal EN_attiny_link = HIGH. WARNING! This signal has to be set LOW before BPi goes to sleep! Hazard of Current flowing in the Rx-Pin of the BPi and destroying it!")
		self._pin_interface.enable_receiving_messages_from_attiny()

	def disable_receiving_messages_from_attiny(self):
		self._logger.info("Disabling receiving Messages from SBC by setting signal EN_attiny_link = LOW")
		self._pin_interface.disable_receiving_messages_from_attiny()

	def start_heartbeat(self):
		self.HB = Heartbeat(self._pin_interface.set_heartbeat_high, self._pin_interface.set_heartbeat_low)
		self.HB.start()

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