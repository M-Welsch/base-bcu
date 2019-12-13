import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

GPIO.setup(7, GPIO.OUT) # SW_HDD_ON
test = "turn_off_hdd"
# test = "turn_on_hdd"

if test == "turn_on_hdd":
	GPIO.output(7, GPIO.HIGH) 
	print("set pin 7 to HIGH")
elif test == "turn_off_hdd":
	GPIO.output(7, GPIO.LOW) 
	print("set pin 7 to LOW")

print("exiting")
GPIO.cleanup()