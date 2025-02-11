from enum import Enum

from oresat_libcanopend import DataType, Entry


class CfcProcessorCameraStatus(Enum):
    OFF = 1
    STANDBY = 2
    CAPTURE = 3
    ERROR = 4


class CfcProcessorEntry(Entry):
    CAMERA_STATUS = 0x4000, 0x1, DataType.UINT8, 0, 1, 4, CfcProcessorCameraStatus, None
    CAMERA_NUMBER_TO_CAPTURE = 0x4000, 0x2, DataType.UINT8, 1
    CAMERA_CAPTURE_DELAY = 0x4000, 0x3, DataType.UINT32, 1000
    CAMERA_LAST_CAPTURE = 0x4000, 0x4, DataType.DOMAIN, None
    CAMERA_LAST_DISPLAY_IMAGE = 0x4000, 0x5, DataType.DOMAIN, None
    CAMERA_LAST_CAPTURE_TIME = 0x4000, 0x6, DataType.UINT64, 0
    CAMERA_SAVE_CAPTURES = 0x4000, 0x7, DataType.BOOL, True
    CAMERA_ENABLED = 0x4000, 0x8, DataType.BOOL, False
    CAMERA_INTEGRATION_TIME = 0x4000, 0x9, DataType.UINT32, 0
    CAMERA_TEMPERATURE = 0x4000, 0xA, DataType.INT8, 0
    TEC_STATUS = 0x4001, 0x1, DataType.BOOL, False
    TEC_SATURATED = 0x4001, 0x2, DataType.BOOL, False
    TEC_PID_SETPOINT = 0x4001, 0x3, DataType.INT8, 0
    TEC_PID_KP = 0x4001, 0x4, DataType.FLOAT32, 0.5
    TEC_PID_KI = 0x4001, 0x5, DataType.FLOAT32, 0.0
    TEC_PID_KD = 0x4001, 0x6, DataType.FLOAT32, 0.1
    TEC_PID_DELAY = 0x4001, 0x7, DataType.UINT32, 250
    TEC_MOVING_AVG_SAMPLES = 0x4001, 0x8, DataType.UINT8, 4
    TEC_SATURATION_DIFF = 0x4001, 0x9, DataType.UINT8, 3
    TEC_COOLDOWN_TEMPERATURE = 0x4001, 0xA, DataType.INT8, 40
    TEC_PID_GRAPH = 0x4001, 0xB, DataType.DOMAIN, None


class CfcProcessorTpdo(Enum):
    TPDO_1 = 0
    TPDO_2 = 1
    TPDO_3 = 2
