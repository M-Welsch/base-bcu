
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
            PinInterface.__instance = PinInterface()
            GPIO.setmode(GPIO.BOARD)
        # this kind of disables the ramp. It sounds best ...
        PinInterface.__instance.step_interval_initial = PinInterface.__instance.step_interval = 0.001
        PinInterface.__instance._initialize_pins()
        return PinInterface.__instance

    def __init__(self):
        raise Exception("This class is a singleton. Use global_instance() instead!")

    def _initialize_pins(self):
        GPIO.setup(Pins.SW_HDD_ON, GPIO.OUT)
        GPIO.setup(Pins.nSensor_Docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.nSensor_Undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.button_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.SW_HDD_OFF, GPIO.OUT)
        GPIO.setup(Pins.Stepper_Step, GPIO.OUT)
        GPIO.setup(Pins.Stepper_Dir, GPIO.OUT)
        GPIO.setup(Pins.Stepper_nReset, GPIO.OUT)
        GPIO.output(Pins.Stepper_Step, GPIO.LOW)
        GPIO.output(Pins.Stepper_Dir, GPIO.LOW)
        GPIO.output(Pins.Stepper_nReset, GPIO.LOW)
        GPIO.setup(Pins.attiny_program_ncommunicate, GPIO.OUT)
        GPIO.setup(Pins.En_attiny_link, GPIO.OUT)
        GPIO.setup(Pins.heartbeat, GPIO.OUT)
        self.set_attiny_serial_path_to_communication()
        self.enable_receiving_messages_from_attiny()

    @staticmethod
    def cleanup():
        GPIO.cleanup()

    @property
    def docked_sensor_pin_high(self):
        return GPIO.input(Pins.nSensor_Docked)

    @property
    def docked(self):
        return not GPIO.input(Pins.nSensor_Docked)

    @property
    def undocked(self):
        return not GPIO.input(Pins.nSensor_Undocked)

    @property
    def undocked_sensor_pin_high(self):
        return GPIO.input(Pins.nSensor_Undocked)

    @property
    def button_0_pin_high(self):
        return GPIO.input(Pins.button_0)

    @property
    def button_1_pin_high(self):
        return GPIO.input(Pins.button_1)

    @staticmethod
    def activate_hdd_pin():
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        GPIO.output(Pins.SW_HDD_ON, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(Pins.SW_HDD_ON, GPIO.LOW)

    @staticmethod
    def deactivate_hdd_pin():
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        GPIO.output(Pins.SW_HDD_OFF, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(Pins.SW_HDD_OFF, GPIO.LOW)

    @staticmethod
    def set_motor_pins_for_braking():
        GPIO.output(Pins.Motordriver_L, GPIO.LOW)
        GPIO.output(Pins.Motordriver_R, GPIO.LOW)

    @staticmethod
    def set_motor_pins_for_docking():
        GPIO.output(Pins.Motordriver_L, GPIO.HIGH)
        GPIO.output(Pins.Motordriver_R, GPIO.LOW)

    @staticmethod
    def set_motor_pins_for_undocking():
        GPIO.output(Pins.Motordriver_L, GPIO.LOW)
        GPIO.output(Pins.Motordriver_R, GPIO.HIGH)

    def stepper_driver_on(self):
        self.set_nreset_pin_high()
        self.step_interval = self.step_interval_initial

    def stepper_driver_off(self):
        self.set_nreset_pin_low()
        self.step_interval = self.step_interval_initial

    @staticmethod
    def set_nreset_pin_high():
        GPIO.output(Pins.Stepper_nReset, GPIO.HIGH)

    @staticmethod
    def set_nreset_pin_low():
        GPIO.output(Pins.Stepper_nReset, GPIO.LOW)

    def stepper_step(self):
        self.set_step_pin_high()
        sleep(self.step_interval)
        self.set_step_pin_low()
        sleep(self.step_interval)

        if self.step_interval > 0.0005:
            PinInterface.step_interval = self.step_interval/1.2

    @staticmethod
    def set_step_pin_high():
        GPIO.output(Pins.Stepper_Step, GPIO.HIGH)

    @staticmethod
    def set_step_pin_low():
        GPIO.output(Pins.Stepper_Step, GPIO.LOW)

    def stepper_direction_docking(self):
        self.set_direction_pin_high()

    def stepper_direction_undocking(self):
        self.set_direction_pin_low()

    @staticmethod
    def set_direction_pin_high():
        GPIO.output(Pins.Stepper_Dir, GPIO.HIGH)

    @staticmethod
    def set_direction_pin_low():
        GPIO.output(Pins.Stepper_Dir, GPIO.LOW)

    @staticmethod
    def set_attiny_serial_path_to_sbc_fw_update():
        GPIO.output(Pins.attiny_program_ncommunicate, GPIO.HIGH)

    @staticmethod
    def set_attiny_serial_path_to_communication():
        GPIO.output(Pins.attiny_program_ncommunicate, GPIO.LOW)

    @staticmethod
    def enable_receiving_messages_from_attiny():
        GPIO.output(Pins.En_attiny_link, GPIO.HIGH)

    @staticmethod
    def disable_receiving_messages_from_attiny():
        GPIO.output(Pins.En_attiny_link, GPIO.LOW)

    @staticmethod
    def set_heartbeat_high():
        GPIO.output(Pins.heartbeat, GPIO.HIGH)

    @staticmethod
    def set_heartbeat_low():
        GPIO.output(Pins.heartbeat, GPIO.LOW)


class Pins:
    SW_HDD_ON = 7
    SW_HDD_OFF = 18
    nSensor_Docked = 13
    nSensor_Undocked = 11
    Stepper_Step = 15
    Stepper_Dir = 19
    Stepper_nReset = 12
    button_0 = 21
    button_1 = 23
    hw_Rev2_nRev3 = 26
    sbu_program_ncommunicate = 16
    En_attiny_link = 22
    Heartbeat = 24
