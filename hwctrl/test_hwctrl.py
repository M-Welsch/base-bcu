from hwctrl import *

def write_out(msg):
	print(msg)

hwctrl = HWCTRL.global_instance(write_out)
hwctrl.start()
input("Press enter to quit ..")
hwctrl.terminate()