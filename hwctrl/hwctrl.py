# creen
# creenShots
# XcreenShots
# ScreenShots

import json
import time
from threading import Thread, Timer
from queue import Queue
import smbus
import RPi.GPIO as GPIO

from base.hwctrl.lcd import *
from base.common.base_queues import Current_Queue

# physical (!) pin definitions (update after schematic change!!)
class Pin:
	SW_HDD_ON = 7
	Dis_RS = 8
	Dis_E = 10
	Dis_DB4 = 12
	Dis_DB5 = 16
	Dis_DB6 = 18
	Dis_DB7 = 22
	Dis_PWM_Gate = 24
	nSensor_Docked = 13
	nSensor_Undocked = 11
	Motordriver_L = 15
	Motordriver_R = 19
	button_0 = 21
	button_1 = 23


class PinInterface:
	def __init__(self, display_default_brightness, display_default_pw=80):
		GPIO.setmode(GPIO.BOARD)

		GPIO.setup(Pin.SW_HDD_ON, GPIO.OUT)
		GPIO.setup(Pin.Motordriver_R, GPIO.OUT)
		GPIO.setup(Pin.Motordriver_L, GPIO.OUT)
		GPIO.output(Pin.Motordriver_L, GPIO.LOW)
		GPIO.output(Pin.Motordriver_R, GPIO.LOW)

		GPIO.setup(Pin.nSensor_Docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(Pin.nSensor_Undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(Pin.button_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(Pin.button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		GPIO.setup(Pin.Dis_PWM_Gate, GPIO.OUT)
		self.display_PWM = GPIO.PWM(Pin.Dis_PWM_Gate, display_default_pw)
		self.display_PWM.start(display_default_brightness)

	@staticmethod
	def cleanup():
		GPIO.cleanup()

	@property
	def status(self):
		return {
			"button_0_pr": self.button_0_pin_high,
			"button_1_pr": self.button_1_pin_high,
			"sensor_undocked": self.undocked_sensor_pin_high,
			"sensor_docked": self.docked_sensor_pin_high,
			"Motordriver_L": GPIO.input(Pin.Motordriver_L),
			"Motordriver_R": GPIO.input(Pin.Motordriver_R),
			"SW_HDD_ON": GPIO.input(Pin.SW_HDD_ON)
		}

	@property
	def docked_sensor_pin_high(self):
		return GPIO.input(Pin.nSensor_Docked)

	@property
	def undocked_sensor_pin_high(self):
		return GPIO.input(Pin.nSensor_Undocked)

	@property
	def button_0_pin_high(self):
		return GPIO.input(Pin.button_0)

	@property
	def button_1_pin_high(self):
		return GPIO.input(Pin.button_1)
	
	@staticmethod
	def activate_hdd_pin():
		GPIO.output(Pin.SW_HDD_ON, GPIO.HIGH)

	@staticmethod
	def deactivate_hdd_pin():
		GPIO.output(Pin.SW_HDD_ON, GPIO.LOW)
	
	@staticmethod
	def set_motor_pins_for_braking():
		GPIO.output(Pin.Motordriver_L, GPIO.LOW)
		GPIO.output(Pin.Motordriver_R, GPIO.LOW)
	
	@staticmethod
	def set_motor_pins_for_docking():
		GPIO.output(Pin.Motordriver_L, GPIO.HIGH)
		GPIO.output(Pin.Motordriver_R, GPIO.LOW)

	@staticmethod
	def set_motor_pins_for_undocking():
		GPIO.output(Pin.Motordriver_L, GPIO.LOW)
		GPIO.output(Pin.Motordriver_R, GPIO.HIGH)


class Current_Measurement(Thread):
	def __init__(self, sampling_interval):
		print("Current Sensor is initializing")
		super(Current_Measurement, self).__init__()
		self._samling_interval = sampling_interval
		self._bus = smbus.SMBus(1)
		self._exit_flag = False
		self._peak_current = 0
		self._current = 0
		self._current_q = Current_Queue(maxsize=100)

	def run(self):
		self._exit_flag = False
		while not self._exit_flag: 
			data = self._bus.read_i2c_block_data(0x4d,1)
			self._current = int(str(data[0]) + str(data[1]))
			self._current_q.put_current(self._current)
			if self.current > self._peak_current: self._peak_current = self._current
			sleep(self._samling_interval)

	@property
	def current(self):
		return self._current

	@property
	def peak_current(self):
		return self._peak_current

	@property
	def avg_current_10sec(self):
		qsize = self._current_q.qsize()
		avg_current_10sec = 0
		while not self._current_q.empty():
			avg_current_10sec = avg_current_10sec + self._current_q.get()
		avg_current_10sec = avg_current_10sec / qsize
		return avg_current_10sec
	
	def terminate(self):
		self._exit_flag = True

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

	def dock(self):
		# Motor Forward
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

			# print("Imotor = %s" % current)
			sleep(0.1)
		# brake
		self.pin_interface.set_motor_pins_for_braking()

		peak_current = self.cur_meas.peak_current
		avg_current = self.cur_meas.avg_current_10sec

		print("maximum current: {:.2f}, avg_current_10sec: {:.2f}".format(peak_current, avg_current))
		self.cur_meas.terminate()

		print("Docking Timeout !!!" if flag_docking_timeout else "Docked in %i seconds" % timeDiff)
		self._logger.error("Docking Timeout !!!" if flag_docking_timeout else "Docked in {:.2f} seconds, peak current: {:.2f}, average_current (over max 10s): {:.2f}".format(timeDiff, peak_current, avg_current))

	def undock(self):
		# Motor Backward
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

			# print("Imotor = %s" % self.cur_meas.current)
			sleep(0.1)
		# brake
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
		self.clear()
		self.message("Display up\nand ready")

	@property
	def current_brightness(self):
		return self._current_brightness

	def display(self, msg, duration):
		self._dim(self._default_brightness)
		self._write(msg)
		Timer(duration, lambda: self._dim(0)).start()

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