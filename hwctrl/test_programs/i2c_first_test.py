import smbus
from time import sleep

bus = smbus.SMBus(1)

try:
	while True:
		data = bus.read_i2c_block_data(0x4d, 1)
		print("Data[0] = %r\nData[1] = %r" % (data[0], data[1]))
		sleep(1)
except KeyboardInterrupt:
	pass
