from time import sleep

def Stepper_Tester_wo_hwctrl():
	import RPi.GPIO as GPIO
	stepper_reset = 12
	stepper_step = 15
	stepper_dir = 19
	endswitch_undocked = 11
	endswitch_docked = 13
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(stepper_reset, GPIO.OUT)
	GPIO.setup(stepper_step, GPIO.OUT)
	GPIO.setup(stepper_dir, GPIO.OUT)
	GPIO.setup(endswitch_docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(endswitch_undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	GPIO.output(stepper_step, GPIO.LOW)
	GPIO.output(stepper_reset, GPIO.HIGH)
	GPIO.output(stepper_dir, GPIO.HIGH)

	# go into one direction for a while
	for i in range(1000):
		GPIO.output(stepper_step, GPIO.HIGH)
		sleep(0.0005)
		GPIO.output(stepper_step, GPIO.LOW)
		sleep(0.0005)

	sleep(0.5)
	# go in the other direction for a while
	GPIO.output(stepper_dir, GPIO.LOW)
	for i in range(1000):
		GPIO.output(stepper_step, GPIO.HIGH)
		sleep(0.0005)
		GPIO.output(stepper_step, GPIO.LOW)
		sleep(0.0005)

	GPIO.output(stepper_reset, GPIO.LOW)
	GPIO.cleanup()

if __name__ == "__main__":
	Stepper_Tester_wo_hwctrl()
