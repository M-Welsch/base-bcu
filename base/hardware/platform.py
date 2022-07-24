from platform import machine


def has_sbu() -> bool:
    return machine() == "armv7l"


HAS_SBU: bool = machine() == "armv7l"
