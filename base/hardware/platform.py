from platform import machine

HAS_SBU: bool = machine() == "armv7l"
