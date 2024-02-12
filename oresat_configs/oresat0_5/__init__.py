"""OreSat0.5 object dictionary and beacon constants."""

import os
from typing import Optional

from ..base import (
    BAT_CONFIG_PATH,
    C3_CONFIG_PATH,
    CFC_CONFIG_PATH,
    DXWIFI_CONFIG_PATH,
    FW_COMMON_CONFIG_PATH,
    GPS_CONFIG_PATH,
    IMU_CONFIG_PATH,
    RW_CONFIG_PATH,
    SOLAR_CONFIG_PATH,
    ST_CONFIG_PATH,
    SW_COMMON_CONFIG_PATH,
)

_CONFIGS_DIR = os.path.dirname(os.path.abspath(__file__))

BEACON_CONFIG_PATH: str = f"{_CONFIGS_DIR}/beacon.yaml"

CARD_CONFIGS_PATH: dict[str, Optional[tuple[str, ...]]] = {
    "c3": (C3_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
    "battery_1": (BAT_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_1": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_2": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_3": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_4": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_5": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_6": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "adcs": (IMU_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "rw_1": (RW_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "rw_2": (RW_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "rw_3": (RW_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "rw_4": (RW_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "gps": (GPS_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
    "star_tracker_1": (ST_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
    "dxwifi": (DXWIFI_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
    "cfc_processor": (CFC_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
    "cfc_sensor": None,
}
