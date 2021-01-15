import RPi.GPIO as GPIO

Taster_0 = 21
Taster_1 = 23

GPIO.setmode(GPIO.BOARD)
GPIO.setup(Taster_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(Taster_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

channel = GPIO.wait_for_edge(Taster_0, GPIO.FALLING)
if channel is None:
    print('Timeout occurred')
else:
    print('Edge detected on channel', channel)

GPIO.cleanup()