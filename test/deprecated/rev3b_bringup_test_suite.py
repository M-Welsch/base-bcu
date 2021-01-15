import sys
from datetime import timedelta

path_to_module = "/home/base"
sys.path.append(path_to_module)

from base.sbu_interface.sbu_communicator import *
from base.common.config import Config
from base.common.utils import shutdown_bcu


def warn_user_and_ask_whether_to_continue(warning):
    user_choice = input("{} Continue [y/N]".format(warning))
    if user_choice not in ["y", "Y", "Yes"]:
        return False
    else:
        return True


def create_human_readable_timestamp(seconds):
    f = datetime.now() + timedelta(seconds=seconds)
    return f.strftime('%d.%m.%Y %H:%M')


class Rev3bEndswitchTester:
    def __init__(self, pin_interface):
        self._pin_interface = pin_interface

    def test(self):
        try:
            self.poll_endsw_status_periodically(0.2)
        except KeyboardInterrupt:
            print("End.")

    def poll_endsw_status_periodically(self, period):
        while True:
            self.print_endswitches_status()
            sleep(period)

    def print_endswitches_status(self):
        print(
            "Endsw. Docked: {}, Endsw. Undocked: {} (End w. Ctrl+C)".format(
                self._pin_interface.docked_sensor_pin_high, self._pin_interface.undocked_sensor_pin_high
            )
        )


class Rev3bPushbuttonTester:
    def __init__(self, pin_interface):
        self._pin_interface = pin_interface

    def test(self):
        print("The Pushbuttons can only be read if the sbu has its internal pullups on the button signals activated!")
        try:
            self.poll_button_status_periodically(0.2)
        except KeyboardInterrupt:
            print("End.")

    def poll_button_status_periodically(self, period):
        while True:
            self.print_endswitches_status()
            sleep(period)

    def print_endswitches_status(self):
        print(
            "Button 0: {}, Button 1: {} (End w. Ctrl+C)".format(
                self._pin_interface.button_0_pin_high, self._pin_interface.button_1_pin_high
            )
        )


class Rev3bStepperTester:
    def __init__(self, pin_interface):
        self._pin_interface = pin_interface

    def test(self):
        if warn_user_and_ask_whether_to_continue(
            "Stepper Tester: Warning. This test moves the stepper. First in docking, then in undocking direction. "
            "However it doesn't care about the endswitches!"
        ):
            self.active_stepper_driver()
            self.move_towards_docking()
            self.move_towards_undocking()
            self.deactivate_stepper_driver()
        else:
            print("Stepper Tester: aborting ...")

    def active_stepper_driver(self):
        self._pin_interface.stepper_driver_on()

    def move_towards_docking(self):
        print("Stepper Tester: Moving towords Dock Position")
        self._pin_interface.stepper_direction_docking()
        for i in range(200):
            self._pin_interface.stepper_step()

    def move_towards_undocking(self):
        print("Stepper Tester: Moving towords Undock Position")
        self._pin_interface.stepper_direction_undocking()
        for i in range(200):
            self._pin_interface.stepper_step()

    def deactivate_stepper_driver(self):
        self._pin_interface.stepper_driver_off()


class Rev3bSerialReceiveTester:
    def __init__(self, hwctrl):
        self._sbuC = self._init_sbu_communicator(hwctrl)

    def test(self):
        print("This test only print outs the Heartbeat Count sent by the sbu")
        try:
            self._writeout_from_sbu_queue_periodically(0.2)
        except KeyboardInterrupt:
            self._sbuC.terminate()
            print("End.")

    def _init_sbu_communicator(self, hwctrl):
        self._from_sbu_queue = []
        self._to_sbu_queue = []
        sbu_c = SbuCommunicator.global_instance()
        sbu_c.start()
        return sbu_c

    def _writeout_from_sbu_queue_periodically(self, period):
        while True:
            while self._from_sbu_queue:
                print(self._from_sbu_queue.pop())
            sleep(period)


class Rev3bDockingUndockingTester:
    def __init__(self, hwctrl):
        self._hwctrl = hwctrl

    def test(self):
        if warn_user_and_ask_whether_to_continue(
            "Docks and undocks the SATA-Connection. It senses the endswitches and otherwise waits for timeout. "
            "If the endswitches don't work, it may damage your BaSe mechanically!"
        ):
            self._hwctrl.dock()
            self._hwctrl.undock()


class Rev3bPowerHddTester:
    def __init__(self, hwctrl):
        self._hwctrl = hwctrl

    def test(self):
        if warn_user_and_ask_whether_to_continue(
            "Powers the HDD. This will apply 12V and 5V on some pins of the SATA Adapter!"
        ):
            self._hwctrl.hdd_power_on()
        if warn_user_and_ask_whether_to_continue(
            "Unowers the HDD. Please make sure, the HDD (if any) is properly unmounted!"
        ):
            self._hwctrl.hdd_power_off()


class Rev3bSerialSendTesterWoHwctrl:
    def __init__(self):
        pass


class Rev3bDockTester:
    def __init__(self, hwctrl):
        self._hwctrl = hwctrl

    def test(self):
        if warn_user_and_ask_whether_to_continue(
            "Docks and undocks the SATA-Connection. It senses the endswitches and otherwise waits for timeout. "
            "If the endswitches don't work, it may damage your BaSe mechanically!"
        ):
            self._hwctrl.dock()


class Rev3bSbuTester:
    def __init__(self, hwctrl, config_sbuc):
        self._sbu_c = self._init_sbu_communicator(hwctrl, config_sbuc)

    @staticmethod
    def _init_sbu_communicator():
        sbu_c = SbuCommunicator.global_instance()
        while not sbu_c.sbu_ready:
            sleep(0.1)
        return sbu_c


class Rev3bSbuCommunicationTester(Rev3bSbuTester):
    def __init__(self, hwctrl, config_sbuc):
        super(Rev3bSbuCommunicationTester, self).__init__(hwctrl, config_sbuc)

    def test(self):
        current = self._measure_current()
        vcc3v = self._measure_vcc3v()
        self._test_write_display(current, vcc3v)
        self._sbu_c.terminate()

    def _measure_current(self):
        print("SBU Communicator Testcase: Current Measurement")
        current = self._sbu_c.current_measurement()
        print(f"Current Measurement Result: {current}A")
        return current

    def _measure_vcc3v(self):
        print("SBU Communicator Testcase: VCC3V3_SBY Measurement")
        vcc3v = self._sbu_c.vcc3v_measurement()
        print(f"VCC3V3_SBY Measurement Result: {vcc3v}V")
        return vcc3v

    def _test_write_display(self, current, vcc3v):
        print("SBU Communicator Testcase: Write to Display")
        self._sbu_c.write_to_display(f"Iin = {current:.2f}A", f"VCC3V = {vcc3v:.2f}V")


class Rev3bSbuShutdownProcessTester(Rev3bSbuTester):
    def __init__(self, hwctrl, config_sbuc):
        super(Rev3bSbuShutdownProcessTester, self).__init__(hwctrl, config_sbuc)

    def test(self):
        if warn_user_and_ask_whether_to_continue("This will shutdown the BCU! Is everything saved?"):
            self._sbu_c.send_shutdown_request()
            self._sbu_c.terminate()
            shutdown_bcu()


class Rev3bSbuSendHrTimestampTester(Rev3bSbuTester):
    def __init__(self, hwctrl, config_sbuc):
        super(Rev3bSbuSendHrTimestampTester, self).__init__(hwctrl, config_sbuc)

    def test(self):
        wake_after = 300  # seconds
        timestamp_hr = create_human_readable_timestamp(wake_after)
        self._sbu_c.send_human_readable_timestamp_next_bu(timestamp_hr)


class Rev3bSbuSendSecondsToNextBuTester(Rev3bSbuTester):
    def __init__(self, hwctrl, config_sbuc):
        super(Rev3bSbuSendSecondsToNextBuTester, self).__init__(hwctrl, config_sbuc)

    def test(self):
        self._sbu_c.send_seconds_to_next_bu_to_sbu(2097152)


class Rev3bSbuShutdownAndWakeAfter500sTester(Rev3bSbuTester):
    def __init__(self, hwctrl, config_sbuc):
        super(Rev3bSbuShutdownAndWakeAfter500sTester, self).__init__(hwctrl, config_sbuc)

    def test(self):
        wake_after = 120*32  # seconds * 32. Factor 32 because for debugging purposes the rtc counts 32 times as fast
        timestamp_hr = create_human_readable_timestamp(wake_after)
        self._sbu_c.send_human_readable_timestamp_next_bu(timestamp_hr)
        self._sbu_c.send_seconds_to_next_bu_to_sbu(wake_after)
        self._sbu_c.send_shutdown_request()
        shutdown_bcu()


class Rev3bSbuDisplayDimmingTester(Rev3bSbuTester):
    def __init__(self, hwctrl, config_sbuc):
        super().__init__(hwctrl, config_sbuc)

    def test(self):
        for i in range(100, 0, -10):
            self._sbu_c.set_display_brightness_percent(i)
        for i in range(0, 100, 10):
            self._sbu_c.set_display_brightness_percent(i)


class Rev3bSbuHmiLedDimmingTester(Rev3bSbuTester):
    def __init__(self, hwctrl, config_sbuc):
        super().__init__(hwctrl, config_sbuc)

    def test(self):
        for i in range(100, 0, -10):
            self._sbu_c.set_led_brightness_percent(i)
        for i in range(0, 100, 10):
            self._sbu_c.set_led_brightness_percent(i)


class Rev3bBringupTestSuite:
    def __init__(self):
        self.display_brightness = 1
        self._pin_interface = PinInterface(self.display_brightness)
        self.testcases = {
            "test_endswitches": ["0", "test_endswitches"],
            "test_pushbuttons": ["1", "test_pushbuttons"],
            "test_stepper": ["2", "test_stepper"],
            "test_sbu_heartbear_receive": ["3", "test_sbu_heartbear_receive"],
            "rev3b_docking_undocking_test": ["4", "rev3b_docking_undocking_test"],
            "rev3b_power_hdd_test": ["5", "rev3b_power_hdd_test"],
            "rev3b_serial_send_tester_wo_hwctrl": ["6", "rev3b_serial_send_tester_wo_hwctrl"],
            "rev3b_dock_test": ["7", "rev3b_dock_test"],
            "rev3b_sbu_communication_tester": ["8", "rev3b_sbu_communication_tester"],
            "rev3b_sbu_shutdown_process_tester": ["9", "rev3b_sbu_shutdown_process_tester"],
            "rev3b_sbu_send_hr_timestamp_tester": ["a", "rev3b_sbu_send_hr_timestamp_tester"],
            "rev3b_sbu_send_seconds_to_next_bu_tester": ["b", "rev3b_sbu_send_seconds_to_next_bu_tester"],
            "rev3b_sbu_shutdown_and_wake_after_500s_tester": ["c", "rev3b_sbu_shutdown_and_wake_after_500s_tester"],
            "rev3b_sbu_display_dimming_tester": ["d", "rev3b_sbu_display_dimming_tester"],
            "rev3b_sbu_hmi_led_dimming_tester": ["e", "rev3b_sbu_hmi_led_dimming_tester"]
        }

        self._config = Config("/home/base/base/config.json")
        self._hwctrl = self._init_hwctrl()

    def _init_hwctrl(self):
        return HWCTRL.global_instance(self._config.config_hwctrl)

    def run(self):
        tester = None
        exitflag = False
        while not exitflag:
            user_choice = self.ask_user_for_testcase()
            if user_choice in ["q", "Quit"]:
                exitflag = True

            if user_choice in self.testcases["test_endswitches"]:
                tester = Rev3bEndswitchTester(self._pin_interface)

            if user_choice in ["1", "test_pushbuttons"]:
                tester = Rev3bPushbuttonTester(self._pin_interface)

            if user_choice in ["2", "test_stepper"]:
                tester = Rev3bStepperTester(self._pin_interface)

            if user_choice in ["3", "test_sbu_heartbear_receive"]:
                tester = Rev3bSerialReceiveTester(self._hwctrl)

            if user_choice in ["4", "rev3b_docking_undocking_test"]:
                tester = Rev3bDockingUndockingTester(self._hwctrl)

            if user_choice in ["5", "rev3b_power_hdd_test"]:
                tester = Rev3bPowerHddTester(self._hwctrl)

            if user_choice in ["6", "rev3b_serial_send_tester_wo_hwctrl"]:
                tester = Rev3bSerialSendTesterWoHwctrl()

            if user_choice in ["7", "rev3b_dock_test"]:
                tester = Rev3bDockTester(self._hwctrl)

            if user_choice in ["8", "rev3b_sbu_communication_tester"]:
                tester = Rev3bSbuCommunicationTester(self._hwctrl, self._config.config_sbu_communicator)

            if user_choice in ["9", "rev3b_sbu_shutdown_process_tester"]:
                tester = Rev3bSbuShutdownProcessTester(self._hwctrl, self._config.config_sbu_communicator)

            if user_choice in self.testcases["rev3b_sbu_send_hr_timestamp_tester"]:
                tester = Rev3bSbuSendHrTimestampTester(self._hwctrl, self._config.config_sbu_communicator)

            if user_choice in self.testcases["rev3b_sbu_send_seconds_to_next_bu_tester"]:
                tester = Rev3bSbuSendSecondsToNextBuTester(self._hwctrl, self._config.config_sbu_communicator)

            if user_choice in self.testcases["rev3b_sbu_shutdown_and_wake_after_500s_tester"]:
                tester = Rev3bSbuShutdownAndWakeAfter500sTester(self._hwctrl, self._config.config_sbu_communicator)

            if user_choice in self.testcases["rev3b_sbu_display_dimming_tester"]:
                tester = Rev3bSbuDisplayDimmingTester(self._hwctrl, self._config.config_sbu_communicator)

            if user_choice in self.testcases["rev3b_sbu_hmi_led_dimming_tester"]:
                tester = Rev3bSbuHmiLedDimmingTester(self._hwctrl, self._config.config_sbu_communicator)

            if tester:
                tester.test()
                tester = None

        self._pin_interface.cleanup()
        self._hwctrl.terminate()

    def ask_user_for_testcase(self):
        print("Choose a testcase by number:\n{}".format(self.list_of_testcases()))
        choice = input("Choose wisely: ")
        if choice in self.valid_choices():
            return choice
        else:
            # ask again
            print("Please make a valid choice. {} is invalid.".format(choice))
            self.ask_user_for_testcase()

    def list_of_testcases(self):
        list_of_testcases = ""
        for testcase_name, testcase in self.testcases.items():
            line = f"({testcase[0]}) {testcase[1]}"
            list_of_testcases += line + "\n"
        list_of_testcases += "(q) Quit"
        return list_of_testcases

    def valid_choices(self):
        valid_choices = ["q"]
        for testcase_name, testcase in self.testcases.items():
            valid_choices.extend(testcase)
        return valid_choices


if __name__ == "__main__":
    print(
        """Welcome to the BaSe rev3b Hardware Bringup Test Suite.
This program enables you to test all BaSe specific hardware components."""
    )
    Suite = Rev3bBringupTestSuite()
    Suite.run()
