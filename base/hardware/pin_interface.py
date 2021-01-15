
from time import sleep
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO is not available. Switching to mockup mode")
    from base.mockups.mockupgpio import GPIO


class PinInterface:
    __instance = None

    @classmethod
    def global_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls.__new__(cls)
            GPIO.setmode(GPIO.BOARD)
        # this kind of disables the ramp. It sounds best ...
        cls.__instance.step_interval_initial = cls.__instance.step_interval = 0.001
        cls.__instance._initialize_pins()
        return cls.__instance

    def __init__(self):
        raise Exception("This class is a singleton. Use global_instance() instead!")

    def _initialize_pins(self):
        GPIO.setup(Pins.sw_hdd_on, GPIO.OUT)
        GPIO.setup(Pins.nsensor_docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.nsensor_undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.button_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.sw_hdd_off, GPIO.OUT)
        GPIO.setup(Pins.stepper_step, GPIO.OUT)
        GPIO.setup(Pins.stepper_dir, GPIO.OUT)
        GPIO.setup(Pins.stepper_nreset, GPIO.OUT)
        GPIO.output(Pins.stepper_step, GPIO.LOW)
        GPIO.output(Pins.stepper_dir, GPIO.LOW)
        GPIO.output(Pins.stepper_nreset, GPIO.LOW)
        GPIO.setup(Pins.sbu_program_ncommunicate, GPIO.OUT)
        GPIO.setup(Pins.en_sbu_link, GPIO.OUT)
        GPIO.setup(Pins.heartbeat, GPIO.OUT)
        self.set_sbu_serial_path_to_communication()
        self.enable_receiving_messages_from_sbu()

    @staticmethod
    def cleanup():
        GPIO.cleanup()

    @property
    def docked_sensor_pin_high(self):
        return GPIO.input(Pins.nsensor_docked)

    @property
    def docked(self):
        return not GPIO.input(Pins.nsensor_docked)

    @property
    def undocked(self):
        return not GPIO.input(Pins.nsensor_undocked)

    @property
    def undocked_sensor_pin_high(self):
        return GPIO.input(Pins.nsensor_undocked)

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
        GPIO.output(Pins.sw_hdd_on, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(Pins.sw_hdd_on, GPIO.LOW)

    @staticmethod
    def deactivate_hdd_pin():
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        GPIO.output(Pins.sw_hdd_off, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(Pins.sw_hdd_off, GPIO.LOW)

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
        GPIO.output(Pins.stepper_nreset, GPIO.HIGH)

    @staticmethod
    def set_nreset_pin_low():
        GPIO.output(Pins.stepper_nreset, GPIO.LOW)

    def stepper_step(self):
        self.set_step_pin_high()
        sleep(self.step_interval)
        self.set_step_pin_low()
        sleep(self.step_interval)

        if self.step_interval > 0.0005:
            PinInterface.step_interval = self.step_interval/1.2

    @staticmethod
    def set_step_pin_high():
        GPIO.output(Pins.stepper_step, GPIO.HIGH)

    @staticmethod
    def set_step_pin_low():
        GPIO.output(Pins.stepper_step, GPIO.LOW)

    def stepper_direction_docking(self):
        self.set_direction_pin_high()

    def stepper_direction_undocking(self):
        self.set_direction_pin_low()

    @staticmethod
    def set_direction_pin_high():
        GPIO.output(Pins.stepper_dir, GPIO.HIGH)

    @staticmethod
    def set_direction_pin_low():
        GPIO.output(Pins.stepper_dir, GPIO.LOW)

    @staticmethod
    def set_sbu_serial_path_to_sbu_fw_update():
        GPIO.output(Pins.sbu_program_ncommunicate, GPIO.HIGH)

    @staticmethod
    def set_sbu_serial_path_to_communication():
        GPIO.output(Pins.sbu_program_ncommunicate, GPIO.LOW)

    @staticmethod
    def enable_receiving_messages_from_sbu():
        GPIO.output(Pins.en_sbu_link, GPIO.HIGH)

    @staticmethod
    def disable_receiving_messages_from_sbu():
        GPIO.output(Pins.en_sbu_link, GPIO.LOW)

    @staticmethod
    def set_heartbeat_high():
        GPIO.output(Pins.heartbeat, GPIO.HIGH)

    @staticmethod
    def set_heartbeat_low():
        GPIO.output(Pins.heartbeat, GPIO.LOW)


class Pins:
    sw_hdd_on = 7
    sw_hdd_off = 18
    nsensor_docked = 13
    nsensor_undocked = 11
    stepper_step = 15
    stepper_dir = 19
    stepper_nreset = 12
    button_0 = 21
    button_1 = 23
    hw_rev2_nrev3 = 26
    sbu_program_ncommunicate = 16
    en_sbu_link = 22
    heartbeat = 24
