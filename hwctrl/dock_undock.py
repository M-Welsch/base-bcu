import time
from base.hwctrl.current_measurement import Current_Measurement

class DockingError(Exception):
	def __init__(self):
		pass

class DockUndock():
	def __init__(self, pin_interface, display, logger, config, hw_rev):
		self.hw_rev = hw_rev
		self.pin_interface = pin_interface
		self.display = display
		self._logger = logger
		self._config = config

		self.maximum_docking_time = self._config["maximum_docking_time"]
		self.docking_overcurrent_limit = self._config["docking_overcurrent_limit"]

	def dock(self):
		if self.hw_rev == 'rev2':
			self.dock_rev2()
		if self.hw_rev == 'rev3':
			self.dock_rev3()

	def undock(self):
		if self.hw_rev == 'rev2':
			self.undock_rev2()
		if self.hw_rev == 'rev3':
			self.undock_rev3()

	def dock_rev2(self):
		if self.docked():
			self._logger.warning("Tried to dock, but end-switch was already pressed. Skipping dock process.")
			return
		self.display("Docking ...", self.maximum_docking_time + 1)
		start_time = time.time()
		self.cur_meas = Current_Measurement(0.1)
		self.cur_meas.start()
		self.pin_interface.set_motor_pins_for_docking()

		timeDiff = 0
		flag_overcurrent = False
		flag_docking_timeout = False
		while(self.pin_interface.docked_sensor_pin_high and
			    not flag_docking_timeout and
			    not flag_overcurrent):
			timeDiff = time.time()-start_time
			if timeDiff > self.maximum_docking_time:
				flag_docking_timeout = True

			current = self.cur_meas.current
			if current > self.docking_overcurrent_limit:
				print("Overcurrent!!")

			self.display("Docking ...\n {:.2f}s, {:.2f}mA".format(timeDiff, current), 10)
			time.sleep(0.1)

		self.pin_interface.set_motor_pins_for_braking()

		peak_current = self.cur_meas.peak_current
		avg_current = self.cur_meas.avg_current_10sec

		print("maximum current: {:.2f}, avg_current_10sec: {:.2f}".format(peak_current, avg_current))
		self.cur_meas.terminate()

		print("Docking Timeout !!!" if flag_docking_timeout else "Docked in %i seconds" % timeDiff)
		self._logger.error("Docking Timeout !!!" if flag_docking_timeout else "Docked in {:.2f} seconds, peak current: {:.2f}, average_current (over max 10s): {:.2f}".format(timeDiff, peak_current, avg_current))

	def dock_rev3(self):
		self.pin_interface.stepper_driver_on()
		self.pin_interface.stepper_direction_docking()

		time_start = time.time()
		while not self.pin_interface.docked:
			self.check_for_timeout(time_start)
			self.pin_interface.stepper_step()
		self.pin_interface.stepper_driver_off()

	def undock_rev3(self):
		self.pin_interface.stepper_driver_on()
		self.pin_interface.stepper_direction_undocking()

		time_start = time.time()
		while not self.pin_interface.undocked:
			self.check_for_timeout(time_start)
			self.pin_interface.stepper_step()
		self.pin_interface.stepper_driver_off()

	def check_for_timeout(self, time_start):
		if time.time() - time_start > self.maximum_docking_time:
			raise DockingError

	def undock_rev2(self):
		if self.undocked():
			self._logger.warning("Tried to undock, but end-switch was already pressed. Skipping undock process.")
			return
		self.display("Undocking ...", self.maximum_docking_time + 1)
		start_time = time.time()
		self.cur_meas = Current_Measurement(0.1)
		self.cur_meas.start()
		self.pin_interface.set_motor_pins_for_undocking()

		timeDiff = 0
		flag_overcurrent = False
		flag_docking_timeout = False
		while(self.pin_interface.undocked_sensor_pin_high and not flag_docking_timeout and not flag_overcurrent):
			timeDiff = time.time()-start_time
			if timeDiff > self.maximum_docking_time:
				flag_docking_timeout = True

			current = self.cur_meas.current
			if current > self.docking_overcurrent_limit:
				print("Overcurrent!!")

			self.display("Undocking ...\n {:.2f}s, {:.2f}mA".format(timeDiff, current), 10)
			time.sleep(0.1)

		self.pin_interface.set_motor_pins_for_braking()

		peak_current = self.cur_meas.peak_current
		avg_current = self.cur_meas.avg_current_10sec
		self.cur_meas.terminate()

		print("maximum current: {:.2f}, avg_current_10sec: {:.2f}".format(peak_current, avg_current))

		self._logger.error("Docking Timeout !!!" if flag_docking_timeout else "Docked in {:.2f} seconds, peak current: {:.2f}, average_current (over max 10s): {:.2f}".format(timeDiff, peak_current, avg_current))

		if flag_docking_timeout:
			print("Undocking Timeout !!!")
		else:
			print("Undocked in %i seconds" % timeDiff)

	def docked(self):
		return not self.pin_interface.docked_sensor_pin_high

	def undocked(self):
		return not self.pin_interface.undocked_sensor_pin_high