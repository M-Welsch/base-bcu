import RPi.GPIO as GPIO

class Pin_Assignment():
	def __init__(self, hw_rev):
		self.hw_rev = hw_rev
		print("Setting up for hw {}".format(hw_rev))

		self.Pin_SW_HDD_ON = {'rev1':7, 'rev2':7}
		self.Pin_Dis_RS = {'rev1':8, 'rev2':27}
		self.Pin_Dis_E = {'rev1':10, 'rev2':28}
		self.Pin_Dis_DB4 = {'rev1':12, 'rev2':12}
		self.Pin_Dis_DB5 = {'rev1':16, 'rev2':16}
		self.Pin_Dis_DB6 = {'rev1':18, 'rev2':18}
		self.Pin_Dis_DB7 = {'rev1':22, 'rev2':22}
		self.Pin_Dis_PWM_Gate = {'rev1':24, 'rev2':24}
		self.Pin_nSensor_Docked = {'rev1':13, 'rev2':13}
		self.Pin_nSensor_Undocked = {'rev1':11, 'rev2':11}
		self.Pin_Motordriver_L = {'rev1':15, 'rev2':None}
		self.Pin_Motordriver_R = {'rev1':19, 'rev2':None}
		self.Pin_Stepper_Step = {'rev1':None, 'rev2':15}
		self.Pin_Stepper_Dir = {'rev1':None, 'rev2':19}
		self.Pin_Stepper_nReset = {'rev1':None, 'rev2':31}
		self.Pin_button_0 = {'rev1':21, 'rev2':21}
		self.Pin_button_1 = {'rev1':23, 'rev2':23}
		self.Pin_hw_Rev1_nRev2 = {'rev1':26, 'rev2':26}

	@property
	def SW_HDD_ON(self):
		return self.Pin_SW_HDD_ON[self.hw_rev]
	
	@property
	def Dis_RS(self):
		return self.Pin_Dis_RS[self.hw_rev]

	@property
	def Dis_E(self):
		return self.Pin_Dis_E[self.hw_rev]

	@property
	def Dis_DB4(self):
		return self.Pin_Dis_DB4[self.hw_rev]

	@property
	def Dis_DB5(self):
		return self.Pin_Dis_DB5[self.hw_rev]

	@property
	def Dis_DB6(self):
		return self.Pin_Dis_DB6[self.hw_rev]

	@property
	def Dis_DB7(self):
		return self.Pin_Dis_DB7[self.hw_rev]

	@property
	def Dis_PWM_Gate(self):
		return self.Pin_Dis_PWM_Gate[self.hw_rev]

	@property
	def nSensor_Docked(self):
		return self.Pin_nSensor_Docked[self.hw_rev]

	@property
	def nSensor_Undocked(self):
		return self.Pin_nSensor_Undocked[self.hw_rev]

	@property
	def Motordriver_L(self):
		return self.Pin_Motordriver_L[self.hw_rev]

	@property
	def Motordriver_R(self):
		return self.Pin_Motordriver_R[self.hw_rev]

	@property
	def Stepper_Step(self):
		return self.Pin_Stepper_Step[self.hw_rev]

	@property
	def Stepper_Dir(self):
		return self.Pin_Stepper_Dir[self.hw_rev]

	@property
	def Stepper_nReset(self):
		return self.Pin_Stepper_nReset[self.hw_rev]

	@property
	def button_0(self):
		return self.Pin_button_0[self.hw_rev]

	@property
	def button_1(self):
		return self.Pin_button_1[self.hw_rev]

	@property
	def hw_Rev1_nRev2(self):
		return self.Pin_hw_Rev1_nRev2[self.hw_rev]

class PinInterface():
	def __init__(self, display_default_brightness, display_default_pw=80):
		GPIO.setmode(GPIO.BOARD)
		hw_rev = self.get_hw_revision()
		self.pin = Pin_Assignment(hw_rev)

		GPIO.setup(self.pin.SW_HDD_ON, GPIO.OUT)
		if hw_rev == 'rev1':
			GPIO.setup(self.pin.Motordriver_R, GPIO.OUT)
			GPIO.setup(self.pin.Motordriver_L, GPIO.OUT)
			GPIO.output(self.pin.Motordriver_L, GPIO.LOW)
			GPIO.output(self.pin.Motordriver_R, GPIO.LOW)

		if hw_rev == 'rev2':
			GPIO.setup(self.pin.Stepper_Step, GPIO.OUT)
			GPIO.setup(self.pin.Stepper_Dir, GPIO.OUT)
			GPIO.setup(self.pin.Stepper_nReset, GPIO.OUT)

			GPIO.output(self.pin.Stepper_Step, GPIO.LOW)
			GPIO.output(self.pin.Stepper_Dir, GPIO.LOW)
			GPIO.output(self.pin.Stepper_nReset, GPIO.LOW)


		GPIO.setup(self.pin.nSensor_Docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.pin.nSensor_Undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.pin.button_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.pin.button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)


		GPIO.setup(self.pin.Dis_PWM_Gate, GPIO.OUT)
		self.display_PWM = GPIO.PWM(self.pin.Dis_PWM_Gate, display_default_pw)
		self.display_PWM.start(display_default_brightness)

	def get_hw_revision(self):
		GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		if GPIO.input(26):
			# in HW revision 1 (With LEGO Motor) pin 26 is floating and will be read HIGH with the internal pullup
			return "rev1"
		else:
			# in HW revision 2 (With Sepper) Pin 26 is shorted to GND
			return "rev2"
		# deactivate pullup to save some power
		GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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
			"Motordriver_L": GPIO.input(self.pin.Motordriver_L),
			"Motordriver_R": GPIO.input(self.pin.Motordriver_R),
			"SW_HDD_ON": GPIO.input(self.pin.SW_HDD_ON)
		}

	@property
	def docked_sensor_pin_high(self):
		return GPIO.input(self.pin.nSensor_Docked)

	@property
	def undocked_sensor_pin_high(self):
		return GPIO.input(self.pin.nSensor_Undocked)

	@property
	def button_0_pin_high(self):
		return GPIO.input(self.pin.button_0)

	@property
	def button_1_pin_high(self):
		return GPIO.input(self.pin.button_1)
	
	def activate_hdd_pin(self):
		GPIO.output(self.pin.SW_HDD_ON, GPIO.HIGH)

	def deactivate_hdd_pin(self):
		GPIO.output(self.pin.SW_HDD_ON, GPIO.LOW)
	
	def set_motor_pins_for_braking(self):
		GPIO.output(self.pin.Motordriver_L, GPIO.LOW)
		GPIO.output(self.pin.Motordriver_R, GPIO.LOW)
	
	def set_motor_pins_for_docking(self):
		GPIO.output(self.pin.Motordriver_L, GPIO.HIGH)
		GPIO.output(self.pin.Motordriver_R, GPIO.LOW)

	def set_motor_pins_for_undocking(self):
		GPIO.output(self.pin.Motordriver_L, GPIO.LOW)
		GPIO.output(self.pin.Motordriver_R, GPIO.HIGH)