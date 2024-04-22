"""
OreSat OD constants

Seperate from __init__.py to avoid cirular imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum, unique

from . import oresat0, oresat0_5, oresat1
from .base import ConfigPaths

__all__ = [
    "__version__",
    "OreSatId",
    "NodeId",
    "Mission",
    "Consts",
]

try:
    from ._version import version as __version__  # type: ignore
except ImportError:
    __version__ = "0.0.0"  # package is not installed


@dataclass
class Mission:
    """A specific set of constants associated with an OreSat Mission"""

    id: int
    arg: str
    beacon_path: str
    cards_path: ConfigPaths


@unique
class Consts(Mission, Enum):
    """Constants associated with each OreSat Mission"""

    ORESAT0 = 1, "0", oresat0.BEACON_CONFIG_PATH, oresat0.CARD_CONFIGS_PATH
    ORESAT0_5 = 2, "0.5", oresat0_5.BEACON_CONFIG_PATH, oresat0_5.CARD_CONFIGS_PATH
    ORESAT1 = 3, "1", oresat1.BEACON_CONFIG_PATH, oresat1.CARD_CONFIGS_PATH

    def __str__(self) -> str:
        return "OreSat" + self.arg

    @classmethod
    def default(cls) -> Consts:
        """Returns the currently active mission"""
        return cls.ORESAT0_5

    @classmethod
    def from_string(cls, val: str) -> Consts:
        """Fetches the Mission associated with an appropriate string

        Appropriate strings are the arg (0, 0.5, ...), optionally prefixed with
        OreSat or oresat
        """
        arg = val.lower().removeprefix("oresat")
        for m in cls:
            if m.arg == arg:
                return m
        raise ValueError(f"invalid oresat mission: {val}")

    @classmethod
    def from_id(cls, val: OreSatId | int) -> Consts:
        """Fetches the Mission associated with an integer ID"""
        if isinstance(val, OreSatId):
            val = val.value
        elif not isinstance(val, int):
            raise TypeError(f"Unsupported val type: '{type(val)}'")

        for m in cls:
            if m.id == val:
                return m
        raise ValueError(f"invalid OreSatId: {val}")


@unique
class OreSatId(IntEnum):
    """Unique ID for each OreSat."""

    ORESAT0 = 1
    ORESAT0_5 = 2
    ORESAT1 = 3


class NodeId(IntEnum):
    """All the CANopen Node ID for OreSat cards."""

    C3 = 0x01
    BATTERY_1 = 0x04
    BATTERY_2 = 0x08
    SOLAR_MODULE_1 = 0x0C
    SOLAR_MODULE_2 = 0x10
    SOLAR_MODULE_3 = 0x14
    SOLAR_MODULE_4 = 0x18
    SOLAR_MODULE_5 = 0x1C
    SOLAR_MODULE_6 = 0x20
    SOLAR_MODULE_7 = 0x24
    SOLAR_MODULE_8 = 0x28
    STAR_TRACKER_1 = 0x2C
    STAR_TRACKER_2 = 0x30
    GPS = 0x34
    ADCS = 0x38
    REACTION_WHEEL_1 = 0x3C
    REACTION_WHEEL_2 = 0x40
    REACTION_WHEEL_3 = 0x44
    REACTION_WHEEL_4 = 0x48
    DXWIFI = 0x4C
    CFC = 0x50
