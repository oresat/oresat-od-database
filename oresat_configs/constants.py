"""
OreSat OD constants

Seperate from __init__.py to avoid cirular imports.
"""

from enum import IntEnum

__version__ = "0.1.0"


class OreSatId(IntEnum):
    """Unique ID for each OreSat."""

    ORESAT0 = 1
    ORESAT0_5 = 2
    ORESAT1 = 3


ORESAT_NICE_NAMES = {
    OreSatId.ORESAT0: "OreSat0",
    OreSatId.ORESAT0_5: "OreSat0.5",
    OreSatId.ORESAT1: "OreSat1",
}
"""Nice name for OreSat missions."""


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
    IMU = 0x38
    REACTION_WHEEL_1 = 0x3C
    REACTION_WHEEL_2 = 0x40
    REACTION_WHEEL_3 = 0x44
    REACTION_WHEEL_4 = 0x48
    DXWIFI = 0x4C
    CFC = 0x50


NODE_NICE_NAMES = {
    NodeId.C3: "C3",
    NodeId.BATTERY_1: "Battery 1",
    NodeId.BATTERY_2: "Battery 2",
    NodeId.SOLAR_MODULE_1: "Solar Module 1",
    NodeId.SOLAR_MODULE_2: "Solar Module 2",
    NodeId.SOLAR_MODULE_3: "Solar Module 3",
    NodeId.SOLAR_MODULE_4: "Solar Module 4",
    NodeId.SOLAR_MODULE_5: "Solar Module 5",
    NodeId.SOLAR_MODULE_6: "Solar Module 6",
    NodeId.SOLAR_MODULE_7: "Solar Module 7",
    NodeId.SOLAR_MODULE_8: "Solar Module 8",
    NodeId.STAR_TRACKER_1: "Star Tracker 1",
    NodeId.STAR_TRACKER_2: "Star Tracker 2",
    NodeId.GPS: "GPS",
    NodeId.IMU: "IMU",
    NodeId.REACTION_WHEEL_1: "Reaction Wheel 1",
    NodeId.REACTION_WHEEL_2: "Reaction Wheel 2",
    NodeId.REACTION_WHEEL_3: "Reaction Wheel 3",
    NodeId.REACTION_WHEEL_4: "Reaction Wheel 4",
    NodeId.DXWIFI: "DxWiFi",
    NodeId.CFC: "CFC",
}
"""Nice name for CANopen Nodes."""
