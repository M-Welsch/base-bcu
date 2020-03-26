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
from base.hwctrl.lcd import *
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
		
		self.pin_interface = PinInterface(int(self._config["display_default_brightness"]))
		self.lcd = LCD(int(self._config["display_default_brightness"]), self.pin_interface)
		self.display = self.lcd.display

		hw_rev = self.get_hw_revision()
		self.dock_undock = DockUndock(self.pin_interface, self.display, self._logger, self._config, hw_rev)


	def get_hw_revision(self):
		hw_rev = self.pin_interface.get_hw_revision()
		print("HWCTRL recognized HW {}".format(hw_rev))
		return hw_rev

	def run(self):
		while not self.exitflag:
			sleep(1)

	def terminate(self):
		print("HWCTRL shutting down")
		self._logger.info("HWCTRL is shutting down. Current status: {}".format(self._status))
		self.exitflag = True
		self.pin_interface.cleanup()
		if self.cur_meas.is_alive():
			self.cur_meas.terminate()

	def _button_0_pressed(self):
		# buttons are low-active!
		button_0_pressed = not self.pin_interface.button_0_pin_high
		if button_0_pressed:
			self._logger.info("Button 0 pressed")
		return button_0_pressed

	def _button_1_pressed(self):
		# buttons are low-active!
		button_1_pressed = not self.pin_interface.button_1_pin_high
		if button_1_pressed:
			self._logger.info("Button 1 pressed")
		return button_1_pressed

	def pressed_buttons(self):
		return self._button_0_pressed(), self._button_1_pressed()

	def docked(self):
		return not self.pin_interface.docked_sensor_pin_high

	def undocked(self):
		return not self.pin_interface.undocked_sensor_pin_high

	def dock(self):
		self.dock_undock.dock()
		
	def undock(self):
		self.dock_undock.undock()

	def hdd_power_on(self):
		self._logger.info("Powering HDD")
		self.cur_meas = Current_Measurement(1)
		self.cur_meas.start()
		self.pin_interface.activate_hdd_pin()

	def hdd_power_off(self):
		self._logger.info("Unpowering HDD")
		self.pin_interface.deactivate_hdd_pin()
		self.cur_meas.terminate()

	def dock_and_power(self):
		# self.dock()
		self.dock_undock.dock()
		self.hdd_power_on()

	def unpower_and_undock(self):
		self.hdd_power_off()
		sleep(5)
		self.undock()


class LCD(Adafruit_CharLCD):
	def __init__(self, default_brightness, pin_interface):
		super(LCD, self).__init__()
		self._default_brightness = default_brightness
		self._current_brightness = default_brightness
		self._display_PWM = pin_interface.display_PWM
		self._timer = Timer(10, lambda: self._dim(0))
		self.clear()
		self.display("Display up\nand ready",10)

	@property
	def current_brightness(self):
		return self._current_brightness

	def display(self, msg, duration):
		self._dim(self._default_brightness)
		self._write(msg)
		self._set_dim_timer(duration)

	def _set_dim_timer(self, duration):
		if self._timer.isAlive():
			self._timer.cancel()
		self._timer = Timer(duration, lambda: self._dim(0))
		self._timer.start()

	def _write(self, message):
		self.clear()
		self.message(message)

	def _dim(self, brightness):
		if brightness > 100:
			brightness = 100
		elif brightness < 0:
			brightness = 0
		self._current_brightness = brightness
		self._display_PWM.ChangeDutyCycle(brightness)