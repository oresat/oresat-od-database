__version__ = '0.1.0'

from enum import IntEnum


class OreSatId(IntEnum):
    '''Unique ID for each OreSat'''

    ORESAT0 = 1
    ORESAT0_5 = 2
    ORESAT1 = 3


class NodeId(IntEnum):
    '''All the CANopen Node ID for OreSat boards.'''

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
    CFC_PROCESSOR = 0x50


class OpdNodeId(IntEnum):
    '''I2C addresses for all cards on the OPD'''

    BATTERY_1 = 0x18
    GPS = 0x19
    IMU = 0x1A
    DXWIFI = 0x1B
    STAR_TRACKER_1 = 0x1C
    CFC_PROCESSOR = 0x1D
    CFC_SENSOR = 0x1E
    BATTERY_2 = 0x1F
    REACTION_WHEEL_1 = 0x20
    REACTION_WHEEL_2 = 0x21
    REACTION_WHEEL_3 = 0x22
    REACTION_WHEEL_4 = 0x23
