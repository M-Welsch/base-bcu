import time
import logging

from base.hwctrl.current_measurement import Current_Measurement


class DockingError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class DockUndock:
    def __init__(self, pin_interface, config, hw_rev):
        self.hw_rev = hw_rev
        self.pin_interface = pin_interface
        self._config = config

        self.maximum_docking_time = self._config["maximum_docking_time"]
        self.docking_overcurrent_limit = self._config["docking_overcurrent_limit"]

        self.cur_meas = Current_Measurement(0.1)

    def dock(self):
        try:
            if self.hw_rev == 'rev2':
                self.dock_rev2()
            if self.hw_rev == 'rev3':
                self.dock_rev3()
        except DockingError as e:
            logging.error(e)
            print(e)

    def undock(self):
        try:
            if self.hw_rev == 'rev2':
                self.undock_rev2()
            if self.hw_rev == 'rev3':
                self.undock_rev3()
        except DockingError as e:
            logging.error(e)
            print(e)

    def dock_rev2(self):
        if self.docked():
            logging.warning("Tried to dock, but end-switch was already pressed. Skipping dock process.")
            return
        start_time = time.time()
        self.cur_meas.start()
        self.pin_interface.set_motor_pins_for_docking()

        time_diff = 0
        flag_overcurrent = False
        flag_docking_timeout = False
        while(self.pin_interface.docked_sensor_pin_high and
              not flag_docking_timeout and
              not flag_overcurrent):
            time_diff = time.time() - start_time
            if time_diff > self.maximum_docking_time:
                flag_docking_timeout = True

            current = self.cur_meas.current
            if current > self.docking_overcurrent_limit:
                print("Overcurrent!!")

            time.sleep(0.1)

        self.pin_interface.set_motor_pins_for_braking()

        peak_current = self.cur_meas.peak_current
        avg_current = self.cur_meas.avg_current_10sec

        print("maximum current: {:.2f}, avg_current_10sec: {:.2f}".format(peak_current, avg_current))
        self.cur_meas.terminate()

        print("Docking Timeout !!!" if flag_docking_timeout else "Docked in %i seconds" % time_diff)
        logging.error(
            "Docking Timeout !!!" if flag_docking_timeout else
            "Docked in {:.2f} seconds, peak current: {:.2f}, average_current (over max 10s): {:.2f}".format(
                time_diff, peak_current, avg_current
            )
        )

    def dock_rev3(self):
        if not self.pin_interface.docked:
            self.pin_interface.stepper_driver_on()
            self.pin_interface.stepper_direction_docking()

        time_start = time.time()
        while not self.pin_interface.docked:
            self.check_for_timeout(time_start)
            self.pin_interface.stepper_step()
        self.pin_interface.stepper_driver_off()

    def undock_rev3(self):
        if not self.pin_interface.undocked:
            self.pin_interface.stepper_driver_on()
            self.pin_interface.stepper_direction_undocking()

        time_start = time.time()
        while not self.pin_interface.undocked:
            self.check_for_timeout(time_start)
            self.pin_interface.stepper_step()
        self.pin_interface.stepper_driver_off()

    def check_for_timeout(self, time_start):
        diff_time = time.time() - time_start
        if diff_time > self.maximum_docking_time:
            self.pin_interface.stepper_driver_off()
            raise DockingError("Maximum Docking Time exceeded: {}".format(diff_time))

    def undock_rev2(self):
        if self.undocked():
            logging.warning("Tried to undock, but end-switch was already pressed. Skipping undock process.")
            return
        start_time = time.time()
        self.cur_meas = Current_Measurement(0.1)
        self.cur_meas.start()
        self.pin_interface.set_motor_pins_for_undocking()

        time_diff = 0
        flag_overcurrent = False
        flag_docking_timeout = False
        while self.pin_interface.undocked_sensor_pin_high and not flag_docking_timeout and not flag_overcurrent:
            time_diff = time.time()-start_time
            if time_diff > self.maximum_docking_time:
                flag_docking_timeout = True

            current = self.cur_meas.current
            if current > self.docking_overcurrent_limit:
                print("Overcurrent!!")

            time.sleep(0.1)

        self.pin_interface.set_motor_pins_for_braking()

        peak_current = self.cur_meas.peak_current
        avg_current = self.cur_meas.avg_current_10sec
        self.cur_meas.terminate()

        print("maximum current: {:.2f}, avg_current_10sec: {:.2f}".format(peak_current, avg_current))

        logging.error(
            "Docking Timeout !!!" if flag_docking_timeout else
            "Docked in {:.2f} seconds, peak current: {:.2f}, average_current (over max 10s): {:.2f}".format(
                time_diff, peak_current, avg_current
            )
        )

        if flag_docking_timeout:
            print("Undocking Timeout !!!")
        else:
            print("Undocked in %i seconds" % time_diff)

    def docked(self):
        return not self.pin_interface.docked_sensor_pin_high

    def undocked(self):
        return not self.pin_interface.undocked_sensor_pin_high
