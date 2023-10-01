"""OreSat OD constants"""

from enum import IntEnum

__version__ = "0.1.0"


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


class Index(IntEnum):
    """OD posible indexes."""

    # standard object indexes
    PRODUCER_HEARTBEAT_TIME = 0x1017
    OS_COMMAND = 0x1023
    SCET = 0x2010
    UTC = 0x2011
    # OreSat indexes
    COMMON_DATA = 0x3000
    CARD_DATA = 0x6000
    OTHER_CARD_BASE_INDEX = 0x7000
    C3_DATA = OTHER_CARD_BASE_INDEX + NodeId.C3
    BATTERY_1_DATA = OTHER_CARD_BASE_INDEX + NodeId.BATTERY_1
    BATTERY_2_DATA = OTHER_CARD_BASE_INDEX + NodeId.BATTERY_2
    SOLAR_MODULE_1_DATA = OTHER_CARD_BASE_INDEX + NodeId.SOLAR_MODULE_1
    SOLAR_MODULE_2_DATA = OTHER_CARD_BASE_INDEX + NodeId.SOLAR_MODULE_2
    SOLAR_MODULE_3_DATA = OTHER_CARD_BASE_INDEX + NodeId.SOLAR_MODULE_3
    SOLAR_MODULE_4_DATA = OTHER_CARD_BASE_INDEX + NodeId.SOLAR_MODULE_4
    SOLAR_MODULE_5_DATA = OTHER_CARD_BASE_INDEX + NodeId.SOLAR_MODULE_5
    SOLAR_MODULE_6_DATA = OTHER_CARD_BASE_INDEX + NodeId.SOLAR_MODULE_6
    SOLAR_MODULE_7_DATA = OTHER_CARD_BASE_INDEX + NodeId.SOLAR_MODULE_7
    SOLAR_MODULE_8_DATA = OTHER_CARD_BASE_INDEX + NodeId.SOLAR_MODULE_8
    STAR_TRACKER_1_DATA = OTHER_CARD_BASE_INDEX + NodeId.STAR_TRACKER_1
    STAR_TRACKER_2_DATA = OTHER_CARD_BASE_INDEX + NodeId.STAR_TRACKER_2
    GPS_DATA = OTHER_CARD_BASE_INDEX + NodeId.GPS
    IMU_DATA = OTHER_CARD_BASE_INDEX + NodeId.IMU
    REACTION_WHEEL_1_DATA = OTHER_CARD_BASE_INDEX + NodeId.REACTION_WHEEL_1
    REACTION_WHEEL_2_DATA = OTHER_CARD_BASE_INDEX + NodeId.REACTION_WHEEL_2
    REACTION_WHEEL_3_DATA = OTHER_CARD_BASE_INDEX + NodeId.REACTION_WHEEL_3
    REACTION_WHEEL_4_DATA = OTHER_CARD_BASE_INDEX + NodeId.REACTION_WHEEL_4
    DXWIFI_DATA = OTHER_CARD_BASE_INDEX + NodeId.DXWIFI
    CFC_DATA = OTHER_CARD_BASE_INDEX + NodeId.CFC
