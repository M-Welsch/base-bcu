
from time import sleep
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO is not available. Switching to mockup mode")
    from base.mockups.mockupgpio import GPIO


class PinInterface:
    __instance = None

    @staticmethod
    def global_instance():
        if PinInterface.__instance is None:
            PinInterface()
        return PinInterface.__instance

    def __init__(self, display_default_brightness, display_default_pw=80):
        if PinInterface.__instance is not None:
            raise Exception("This class is a singleton!")

        PinInterface.__instance = self

        self.step_interval_initial = 0.001  # this kind of disables the ramp. It sounds best ...
        GPIO.setmode(GPIO.BOARD)
        self._hw_rev = self.get_hw_revision()
        self.pin = _PinAssignment(self._hw_rev)

        self._initialize_common()

        if self._hw_rev == 'rev2':
            self._initialize_rev2_specific(display_default_brightness, display_default_pw)
        elif self._hw_rev == 'rev3':
            self._initialize_rev3_specific()

    def _initialize_common(self):
        GPIO.setup(self.pin.SW_HDD_ON, GPIO.OUT)
        GPIO.setup(self.pin.nSensor_Docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin.nSensor_Undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin.button_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin.button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _initialize_rev2_specific(self, display_default_brightness, display_default_pw):
        GPIO.setup(self.pin.Motordriver_R, GPIO.OUT)
        GPIO.setup(self.pin.Motordriver_L, GPIO.OUT)
        GPIO.output(self.pin.Motordriver_L, GPIO.LOW)
        GPIO.output(self.pin.Motordriver_R, GPIO.LOW)
        GPIO.setup(self.pin.Dis_PWM_Gate, GPIO.OUT)
        self.display_PWM = GPIO.PWM(self.pin.Dis_PWM_Gate, display_default_pw)
        self.display_PWM.start(display_default_brightness)

    def _initialize_rev3_specific(self):
        GPIO.setup(self.pin.SW_HDD_OFF, GPIO.OUT)
        GPIO.setup(self.pin.Stepper_Step, GPIO.OUT)
        GPIO.setup(self.pin.Stepper_Dir, GPIO.OUT)
        GPIO.setup(self.pin.Stepper_nReset, GPIO.OUT)
        GPIO.output(self.pin.Stepper_Step, GPIO.LOW)
        GPIO.output(self.pin.Stepper_Dir, GPIO.LOW)
        GPIO.output(self.pin.Stepper_nReset, GPIO.LOW)
        GPIO.setup(self.pin.attiny_program_ncommunicate, GPIO.OUT)
        GPIO.setup(self.pin.En_attiny_link, GPIO.OUT)
        GPIO.setup(self.pin.heartbeat, GPIO.OUT)
        self.set_attiny_serial_path_to_communication()
        self.enable_receiving_messages_from_attiny()

    def get_hw_revision(self):
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # rev 1 is not respected here.
        if GPIO.input(26):
            # in HW revision 2 (With LEGO Motor) pin 26 is floating and will be read HIGH with the internal pullup
            return "rev2"
        else:
            # in HW revision 3 (rev3a and rev3b - with Sepper) Pin 26 is shorted to GND
            return "rev3"
        # deactivate pullup to save some power
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    @staticmethod
    def cleanup():
        GPIO.cleanup()

    @property
    def status(self):
        return {
            "button_0_pr": self.button_0_pin_high,
            "button_1_pr": self.button_1_pin_high,
            "sensor_undocked": self.undocked_sensor_pin_high,
            "sensor_docked": self.docked_sensor_pin_high,
            "Motordriver_L": GPIO.input(self.pin.Motordriver_L),
            "Motordriver_R": GPIO.input(self.pin.Motordriver_R),
            "SW_HDD_ON": GPIO.input(self.pin.SW_HDD_ON)
        }

    @property
    def docked_sensor_pin_high(self):
        return GPIO.input(self.pin.nSensor_Docked)

    @property
    def docked(self):
        return not GPIO.input(self.pin.nSensor_Docked)

    @property
    def undocked(self):
        return not GPIO.input(self.pin.nSensor_Undocked)

    @property
    def undocked_sensor_pin_high(self):
        return GPIO.input(self.pin.nSensor_Undocked)

    @property
    def button_0_pin_high(self):
        return GPIO.input(self.pin.button_0)

    @property
    def button_1_pin_high(self):
        return GPIO.input(self.pin.button_1)

    def activate_hdd_pin(self):
        if self._hw_rev == 'rev2':
            GPIO.output(self.pin.SW_HDD_ON, GPIO.HIGH)
        if self._hw_rev == 'rev3':
            # rev3 uses a bistable relais with two coils. These have to be powered for at least 4ms. We use 10ms to be safe.
            GPIO.output(self.pin.SW_HDD_ON, GPIO.HIGH)
            sleep(0.1)
            GPIO.output(self.pin.SW_HDD_ON, GPIO.LOW)

    def deactivate_hdd_pin(self):
        if self._hw_rev == 'rev2':
            GPIO.output(self.pin.SW_HDD_ON, GPIO.LOW)
        if self._hw_rev == 'rev3':
            # rev3 uses a bistable relais with two coils. These have to be powered for at least 4ms. We use 10ms to be safe.

            GPIO.output(self.pin.SW_HDD_OFF, GPIO.HIGH)
            sleep(0.1)
            GPIO.output(self.pin.SW_HDD_OFF, GPIO.LOW)

    def set_motor_pins_for_braking(self):
        GPIO.output(self.pin.Motordriver_L, GPIO.LOW)
        GPIO.output(self.pin.Motordriver_R, GPIO.LOW)

    def set_motor_pins_for_docking(self):
        GPIO.output(self.pin.Motordriver_L, GPIO.HIGH)
        GPIO.output(self.pin.Motordriver_R, GPIO.LOW)

    def set_motor_pins_for_undocking(self):
        GPIO.output(self.pin.Motordriver_L, GPIO.LOW)
        GPIO.output(self.pin.Motordriver_R, GPIO.HIGH)

    def stepper_driver_on(self):
        self.set_nreset_pin_high()
        self.step_interval = self.step_interval_initial

    def stepper_driver_off(self):
        self.set_nreset_pin_low()
        self.step_interval = self.step_interval_initial

    def set_nreset_pin_high(self):
        GPIO.output(self.pin.Stepper_nReset, GPIO.HIGH)

    def set_nreset_pin_low(self):
        GPIO.output(self.pin.Stepper_nReset, GPIO.LOW)

    def stepper_step(self):
        self.set_step_pin_high()
        sleep(self.step_interval)
        self.set_step_pin_low()
        sleep(self.step_interval)

        if self.step_interval > 0.0005:
            self.step_interval = self.step_interval/1.2

    def set_step_pin_high(self):
        GPIO.output(self.pin.Stepper_Step, GPIO.HIGH)

    def set_step_pin_low(self):
        GPIO.output(self.pin.Stepper_Step, GPIO.LOW)

    def stepper_direction_docking(self):
        self.set_direction_pin_high()

    def stepper_direction_undocking(self):
        self.set_direction_pin_low()

    def set_direction_pin_high(self):
        GPIO.output(self.pin.Stepper_Dir, GPIO.HIGH)

    def set_direction_pin_low(self):
        GPIO.output(self.pin.Stepper_Dir, GPIO.LOW)

    def set_attiny_serial_path_to_sbc_fw_update(self):
        GPIO.output(self.pin.attiny_program_ncommunicate, GPIO.HIGH)

    def set_attiny_serial_path_to_communication(self):
        GPIO.output(self.pin.attiny_program_ncommunicate, GPIO.LOW)

    def enable_receiving_messages_from_attiny(self):
        GPIO.output(self.pin.En_attiny_link, GPIO.HIGH)

    def disable_receiving_messages_from_attiny(self):
        GPIO.output(self.pin.En_attiny_link, GPIO.LOW)

    def set_heartbeat_high(self):
        GPIO.output(self.pin.heartbeat, GPIO.HIGH)

    def set_heartbeat_low(self):
        GPIO.output(self.pin.heartbeat, GPIO.LOW)


class _PinAssignment:
    def __init__(self, hw_rev):
        self.hw_rev = hw_rev
        # print("Setting up for hw {}".format(hw_rev))

        # General Comments on the changes between rev2 (blue Breadboard) and rev3 (Stepper):
        # Display was moved from BPi to external controller (attiny816 aka SBC)
        # A dual coil latched relais was used that requires two control signals
        self.Pin_SW_HDD_ON = {'rev2': 7, 'rev3': 7}
        self.Pin_SW_HDD_OFF = {'rev2': None, 'rev3': 18}
        self.Pin_Dis_RS = {'rev2': 8, 'rev3': None}
        self.Pin_Dis_E = {'rev2': 10, 'rev3': None}
        self.Pin_Dis_DB4 = {'rev2': 12, 'rev3': None}
        self.Pin_Dis_DB5 = {'rev2': 16, 'rev3': None}
        self.Pin_Dis_DB6 = {'rev2': 18, 'rev3': None}
        self.Pin_Dis_DB7 = {'rev2': 22, 'rev3': None}
        self.Pin_Dis_PWM_Gate = {'rev2': 24, 'rev3': None}
        self.Pin_nSensor_Docked = {'rev2': 13, 'rev3': 13}
        self.Pin_nSensor_Undocked = {'rev2': 11, 'rev3': 11}
        self.Pin_Motordriver_L = {'rev2': 15, 'rev3': None}
        self.Pin_Motordriver_R = {'rev2': 19, 'rev3': None}
        self.Pin_Stepper_Step = {'rev2': None, 'rev3': 15}
        self.Pin_Stepper_Dir = {'rev2': None, 'rev3': 19}
        self.Pin_Stepper_nReset = {'rev2': None, 'rev3': 12}
        self.Pin_button_0 = {'rev2': 21, 'rev3': 21}
        self.Pin_button_1 = {'rev2': 23, 'rev3': 23}
        self.Pin_hw_Rev2_nRev3 = {'rev2': 26, 'rev3': 26}
        self.Pin_atting_program_ncommunicate = {'rev2': None, 'rev3': 16}
        self.Pin_En_attiny_link = {'rev2': None, 'rev3': 22}
        self.Pin_Heartbeat = {'rev2': None, 'rev3': 24}

    @property
    def SW_HDD_ON(self):
        return self.Pin_SW_HDD_ON[self.hw_rev]

    @property
    def SW_HDD_OFF(self):
        return self.Pin_SW_HDD_OFF[self.hw_rev]

    @property
    def Dis_RS(self):
        return self.Pin_Dis_RS[self.hw_rev]

    @property
    def Dis_E(self):
        return self.Pin_Dis_E[self.hw_rev]

    @property
    def Dis_DB4(self):
        return self.Pin_Dis_DB4[self.hw_rev]

    @property
    def Dis_DB5(self):
        return self.Pin_Dis_DB5[self.hw_rev]

    @property
    def Dis_DB6(self):
        return self.Pin_Dis_DB6[self.hw_rev]

    @property
    def Dis_DB7(self):
        return self.Pin_Dis_DB7[self.hw_rev]

    @property
    def Dis_PWM_Gate(self):
        return self.Pin_Dis_PWM_Gate[self.hw_rev]

    @property
    def nSensor_Docked(self):
        return self.Pin_nSensor_Docked[self.hw_rev]

    @property
    def nSensor_Undocked(self):
        return self.Pin_nSensor_Undocked[self.hw_rev]

    @property
    def Motordriver_L(self):
        return self.Pin_Motordriver_L[self.hw_rev]

    @property
    def Motordriver_R(self):
        return self.Pin_Motordriver_R[self.hw_rev]

    @property
    def Stepper_Step(self):
        return self.Pin_Stepper_Step[self.hw_rev]

    @property
    def Stepper_Dir(self):
        return self.Pin_Stepper_Dir[self.hw_rev]

    @property
    def Stepper_nReset(self):
        return self.Pin_Stepper_nReset[self.hw_rev]

    @property
    def button_0(self):
        return self.Pin_button_0[self.hw_rev]

    @property
    def button_1(self):
        return self.Pin_button_1[self.hw_rev]

    @property
    def hw_Rev1_nRev2(self):
        return self.Pin_hw_Rev2_nRev3[self.hw_rev]

    @property
    def attiny_program_ncommunicate(self):
        return self.Pin_atting_program_ncommunicate[self.hw_rev]

    @property
    def En_attiny_link(self):
        return self.Pin_En_attiny_link[self.hw_rev]

    @property
    def heartbeat(self):
        return self.Pin_Heartbeat[self.hw_rev]
