import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

GPIO.setup(11, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(13, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(15, GPIO.OUT) # Motordriver L
GPIO.setup(19, GPIO.OUT) # Motordriver R

#test = "toggle"
#test = "forward_backward"
test = "dock_undock"

if test == "forward_backward":
	GPIO.output(15, GPIO.HIGH) 
	GPIO.output(19, GPIO.LOW)
	print("Moving backward")
	sleep(1)

	GPIO.output(15, GPIO.LOW)
	GPIO.output(19, GPIO.LOW)
	print("pausing")
	sleep(1)

	GPIO.output(15, GPIO.LOW)
	GPIO.output(19, GPIO.HIGH)
	print("Moving forward")
	sleep(1)

	GPIO.output(15, GPIO.LOW)
	GPIO.output(19, GPIO.LOW)
	print("end")

elif test == "toggle":
	print("toggling")
	try:
		while True:
			GPIO.output(15, GPIO.HIGH)
			GPIO.output(19, GPIO.HIGH)
			sleep(1)

			GPIO.output(15, GPIO.LOW)
			GPIO.output(19, GPIO.LOW)
			sleep(1)

	except KeyboardInterrupt:
		pass

elif test == "dock_undock":
	print("docking and undocking ..")
	sleep(2)
	GPIO.output(15, GPIO.LOW)
	GPIO.output(19, GPIO.HIGH)
	print("docking, moving forward")
	while GPIO.input(11):
		pass
	GPIO.output(15, GPIO.LOW)
	GPIO.output(19, GPIO.LOW)
	print("docked")

	sleep(1)
	GPIO.output(15, GPIO.HIGH)
	GPIO.output(19, GPIO.LOW)
	print("undocking, moving backward")
	while GPIO.input(13):
		pass
	GPIO.output(15, GPIO.LOW)
	GPIO.output(19, GPIO.LOW)
	print("docked")

print("exiting")
GPIO.cleanup()