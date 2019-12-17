import json
import time
import threading
from base.hwctrl.lcd import *
import smbus
from queue import Queue

# physical (!) pin definitions (update after schematic change!!)
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
Taster_0 = 21
Taster_1 = 23

class Current_Queue(Queue):
	def __init__(self, maxsize):
		super(Current_Queue, self).__init__(maxsize = maxsize)

	def put_current(self, current_value):
		if self.full():
			self.get()
		self.put(current_value)

class Current_Measurement(threading.Thread):
	def __init__(self):
		print("Current Sensor is initializing")
		threading.Thread.__init__(self)
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
			sleep(0.1)

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
		avg_current_10sec = avg_current_10sec/qsize
		return avg_current_10sec
	

	def terminate(self):
		self._exit_flag = True

class HWCTRL(threading.Thread):
	def __init__(self, hardware_control_feedback_flags, append_to_logfile, GPIO=None):
		super(HWCTRL,self).__init__()
		threading.Thread.__init__(self)
		self._feedback_flags = hardware_control_feedback_flags
		self._append_to_logfile = append_to_logfile

		self.exitflag = False

		# get configuration
		with open('base/config.json', 'r') as jf:
			config = json.load(jf)
		# todo: get overcurrent limits etc. from config file.

		self.maximum_docking_time = 10 #seconds # todo: get from config file.
		self.maximum_motor_current = 150 #empiric # todo: get from config file.

		# init Pins
		import RPi.GPIO as GPIO
		self.GPIO = GPIO
		self.GPIO.setmode(GPIO.BOARD)

		self.GPIO.setup(SW_HDD_ON, GPIO.OUT)
		self.GPIO.setup(Motordriver_R, GPIO.OUT)
		self.GPIO.setup(Motordriver_L, GPIO.OUT)
		self.GPIO.output(Motordriver_L, self.GPIO.LOW)
		self.GPIO.output(Motordriver_R, self.GPIO.LOW)

		self.GPIO.setup(nSensor_Docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.GPIO.setup(nSensor_Undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.GPIO.setup(Taster_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.GPIO.setup(Taster_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		self.GPIO.setup(Dis_PWM_Gate, GPIO.OUT)
		self.dis_Brightness = 0.01
		self.display_PWM = GPIO.PWM(Dis_PWM_Gate, 80)
		self.display_PWM.start(100) # todo: get from config file.

		# init Display
		self.lcd = Adafruit_CharLCD()
		self.lcd.clear()
		self.lcd.message("Display up\nand ready")

	def run(self):
		while not self.exitflag:
			print("T0: {}, T1: {}, SensDock: {}, SensUnd: {}".format(self.button_pressed(Taster_0),
																	 self.button_pressed(Taster_1),
																	 self.GPIO.input(nSensor_Docked),
																	 self.GPIO.input(nSensor_Undocked)))
			if(self.button_pressed(Taster_1)):
				if not self.GPIO.input(nSensor_Docked):
					print("nSensor_Docked = LOW => undocking")
					self.lcd.clear()
					self.lcd.message("Undocking ...")
					self.undock()
				elif not self.GPIO.input(nSensor_Undocked):
					print("nSensor_Undocked = LOW => docking")
					self.lcd.clear()
					self.lcd.message("Docking ...")
					self.dock()
				self.lcd.clear()
				self.lcd.message("Done.")
			sleep(1)

	def terminate(self):
		self.exitflag = True
		self.GPIO.cleanup()
		# TODO: self.cur_meas.terminate() # maybe with try-statement

	def button_pressed(self, button):
		# buttons are low-active!
		return not self.GPIO.input(button)

	def dock(self):
		# Motor Forward
		start_time = time.time()
		self.cur_meas = Current_Measurement()
		self.cur_meas.start()
		self.GPIO.output(Motordriver_L, self.GPIO.HIGH)
		self.GPIO.output(Motordriver_R, self.GPIO.LOW)

		timeDiff = 0
		flag_overcurrent = False
		flag_docking_timeout = False
		while(self.GPIO.input(nSensor_Docked) and not flag_docking_timeout and not flag_overcurrent):
			timeDiff = time.time()-start_time
			if timeDiff > self.maximum_docking_time:
				flag_docking_timeout = True

			current = self.cur_meas.current
			if current > self.maximum_motor_current:
				print("Overcurrent!!")

			print("Imotor = %s" % current)
			sleep(0.1)
		# brake
		self.GPIO.output(Motordriver_L, self.GPIO.LOW)
		self.GPIO.output(Motordriver_R, self.GPIO.LOW)
		print("maximum current: {}, avg_current_10sec: {}".format(self.cur_meas.peak_current, self.cur_meas.avg_current_10sec))
		self.cur_meas.terminate()

		print("Docking Timeout !!!" if flag_docking_timeout else "Docked in %i seconds" % timeDiff)

	def undock(self):
		# Motor Backward
		start_time = time.time()
		self.cur_meas = Current_Measurement()
		self.cur_meas.start()
		self.GPIO.output(Motordriver_L, self.GPIO.LOW)
		self.GPIO.output(Motordriver_R, self.GPIO.HIGH)

		timeDiff = 0
		flag_overcurrent = False
		flag_docking_timeout = False
		while(self.GPIO.input(nSensor_Undocked) and not flag_docking_timeout and not flag_overcurrent):
			timeDiff = time.time()-start_time
			if timeDiff > self.maximum_docking_time:
				flag_docking_timeout = True

			current = self.cur_meas.current
			if current > self.maximum_motor_current:
				print("Overcurrent!!")

			print("Imotor = %s" % self.cur_meas.current)
			sleep(0.1)
		# brake
		self.GPIO.output(Motordriver_L, self.GPIO.LOW)
		self.GPIO.output(Motordriver_R, self.GPIO.LOW)
		print("maximum current: {}, avg_current_10sec: {}".format(self.cur_meas.peak_current, self.cur_meas.avg_current_10sec))

		self.cur_meas.terminate()

		if flag_docking_timeout:
			print("Undocking Timeout !!!")
		else:
			print("Undocked in %i seconds" % timeDiff)

	def write_to_display(self,message):
		self.lcd.clear()
		self.lcd.message(message)

	def dim_display(self,brightness):
		self.dis_Brightness = 0.01
		self.changeDutyCycle(brightness)

	def hdd_power(self,state):
		if state == "on":
			self.GPIO.output(SW_HDD_ON, self.GPIO.HIGH)
		elif state == "off":
			self.GPIO.output(SW_HDD_ON, self.GPIO.LOW)
