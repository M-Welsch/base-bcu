from enum import IntEnum


class Pins(IntEnum):
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
