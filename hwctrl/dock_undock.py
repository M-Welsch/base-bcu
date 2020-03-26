class DockUndock():
	def __init__(self, pin_interface, hw_rev):
		self.hw_rev = hw_rev
		self.pin_interface = pin_interface

	def dock(self):
		if self.hw_rev == 'rev1':
			self.dock_rev1()
		if self.hw_rev == 'rev2':
			self.dock_rev2()

	def dock_rev1(self):
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
			sleep(0.1)

		self.pin_interface.set_motor_pins_for_braking()

		peak_current = self.cur_meas.peak_current
		avg_current = self.cur_meas.avg_current_10sec

		print("maximum current: {:.2f}, avg_current_10sec: {:.2f}".format(peak_current, avg_current))
		self.cur_meas.terminate()

		print("Docking Timeout !!!" if flag_docking_timeout else "Docked in %i seconds" % timeDiff)
		self._logger.error("Docking Timeout !!!" if flag_docking_timeout else "Docked in {:.2f} seconds, peak current: {:.2f}, average_current (over max 10s): {:.2f}".format(timeDiff, peak_current, avg_current))