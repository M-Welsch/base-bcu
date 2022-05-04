from __future__ import annotations

from enum import Enum
from platform import machine


class BaSePlatform(Enum):
    BANANAPI = "BANANAPI"
    PC = "PC"


def who_am_i() -> BaSePlatform:
    if machine() == "armv7l":
        i_am = BaSePlatform("BANANAPI")
    else:
        i_am = BaSePlatform("PC")
    return i_am


def platform_with_sbu() -> bool:
    return who_am_i() == BaSePlatform.BANANAPI
