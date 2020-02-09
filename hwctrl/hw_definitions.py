import RPi.GPIO as GPIO

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