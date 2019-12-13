import RPi.GPIO as GPIO
from time import sleep
import os



GPIO.setmode(GPIO.BOARD)

gpio_pins = [3, 5, 7, 8, 10,11,12,13,15,16,18,19,21,22,23,24,26]
state_old = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
for gpio_pin in gpio_pins:
	GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	print("pin %i: %i" % (gpio_pin, GPIO.input(gpio_pin)))

try:
	while True:
		os.system('clear')
		for gpio_pin in gpio_pins:
			print("pin %i: %i" % (gpio_pin, GPIO.input(gpio_pin)))
		sleep(0.1)
except KeyboardInterrupt:
	pass

print("exiting")
GPIO.cleanup()