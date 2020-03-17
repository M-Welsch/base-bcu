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
		if self.docked():
			self._logger.warning("Tried to dock, but end-switch was already pressed. Skipping dock process.")
			return
		self.display("Docking ...", self.maximum_docking_time + 1)
		start_time = time.time()
		self.cur_meas = Current_Measurement(0.1)
		self.cur_meas.start()
		self.pin_interface.set_motor_pins_for_docking()

		timeDiff = 0
		flag_overcurrent = False
		flag_docking_timeout = False
		while(self.pin_interface.docked_sensor_pin_high and
			    not flag_docking_timeout and
			    not flag_overcurrent):
			timeDiff = time.time()-start_time
			if timeDiff > self.maximum_docking_time:
				flag_docking_timeout = True

			current = self.cur_meas.current
			if current > self.docking_overcurrent_limit:
				print("Overcurrent!!")

			self.display("Docking ...\n {:.2f}s, {:.2f}mA".format(timeDiff, current), 10)
			sleep(0.1)

		self.pin_interface.set_motor_pins_for_braking()

		peak_current = self.cur_meas.peak_current
		avg_current = self.cur_meas.avg_current_10sec

		print("maximum current: {:.2f}, avg_current_10sec: {:.2f}".format(peak_current, avg_current))
		self.cur_meas.terminate()

		print("Docking Timeout !!!" if flag_docking_timeout else "Docked in %i seconds" % timeDiff)
		self._logger.error("Docking Timeout !!!" if flag_docking_timeout else "Docked in {:.2f} seconds, peak current: {:.2f}, average_current (over max 10s): {:.2f}".format(timeDiff, peak_current, avg_current))

	def undock(self):
		if self.undocked():
			self._logger.warning("Tried to undock, but end-switch was already pressed. Skipping undock process.")
			return
		self.display("Undocking ...", self.maximum_docking_time + 1)
		start_time = time.time()
		self.cur_meas = Current_Measurement(0.1)
		self.cur_meas.start()
		self.pin_interface.set_motor_pins_for_undocking()

		timeDiff = 0
		flag_overcurrent = False
		flag_docking_timeout = False
		while(self.pin_interface.undocked_sensor_pin_high and not flag_docking_timeout and not flag_overcurrent):
			timeDiff = time.time()-start_time
			if timeDiff > self.maximum_docking_time:
				flag_docking_timeout = True

			current = self.cur_meas.current
			if current > self.docking_overcurrent_limit:
				print("Overcurrent!!")

			self.display("Undocking ...\n {:.2f}s, {:.2f}mA".format(timeDiff, current), 10)
			sleep(0.1)

		self.pin_interface.set_motor_pins_for_braking()

		peak_current = self.cur_meas.peak_current
		avg_current = self.cur_meas.avg_current_10sec
		self.cur_meas.terminate()

		print("maximum current: {:.2f}, avg_current_10sec: {:.2f}".format(peak_current, avg_current))

		self._logger.error("Docking Timeout !!!" if flag_docking_timeout else "Docked in {:.2f} seconds, peak current: {:.2f}, average_current (over max 10s): {:.2f}".format(timeDiff, peak_current, avg_current))

		if flag_docking_timeout:
			print("Undocking Timeout !!!")
		else:
			print("Undocked in %i seconds" % timeDiff)

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
		self.dock()
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