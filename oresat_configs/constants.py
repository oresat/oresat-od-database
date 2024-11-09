"""
OreSat OD constants

Seperate from __init__.py to avoid cirular imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique

from . import oresat0, oresat0_5, oresat1
from .base import ConfigPaths

__all__ = [
    "__version__",
    "MissionConsts",
    "Mission",
]

try:
    from ._version import version as __version__  # type: ignore
except ImportError:
    __version__ = "0.0.0"  # package is not installed


@dataclass
class MissionConsts:
    """A specific set of constants associated with an OreSat Mission"""

    id: int
    arg: str
    beacon_path: str
    cards_path: ConfigPaths


@unique
class Mission(MissionConsts, Enum):
    """Each OreSat Mission and constant configuration data associated with them"""

    ORESAT0 = 1, "0", oresat0.BEACON_CONFIG_PATH, oresat0.CARD_CONFIGS_PATH
    ORESAT0_5 = 2, "0.5", oresat0_5.BEACON_CONFIG_PATH, oresat0_5.CARD_CONFIGS_PATH
    ORESAT1 = 3, "1", oresat1.BEACON_CONFIG_PATH, oresat1.CARD_CONFIGS_PATH

    def __str__(self) -> str:
        return "OreSat" + self.arg

    def filename(self) -> str:
        """Returns a string safe to use in filenames and other restricted settings.

        All lower case, dots replaced with underscores.
        """
        return str(self).lower().replace(".", "_")

    @classmethod
    def default(cls) -> Mission:
        """Returns the currently active mission"""
        return cls.ORESAT0_5

    @classmethod
    def from_string(cls, val: str) -> Mission:
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
    def from_id(cls, val: int) -> Mission:
        """Fetches the Mission associated with an appropriate ID

        Appropriate IDs are integers 1, 2, ... that corespond to the specific
        mission. Note that these are not the number in the Satellite name.
        """
        for m in cls:
            if m.id == val:
                return m
        raise ValueError(f"invalid oresat mission ID: {val}")
