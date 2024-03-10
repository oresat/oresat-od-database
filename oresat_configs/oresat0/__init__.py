"""OreSat0 object dictionary and beacon constants."""

import os

from ..base import (
    ADCS_CONFIG_PATH,
    BAT_CONFIG_PATH,
    C3_CONFIG_PATH,
    DXWIFI_CONFIG_PATH,
    FW_COMMON_CONFIG_PATH,
    GPS_CONFIG_PATH,
    SOLAR_CONFIG_PATH,
    ST_CONFIG_PATH,
    SW_COMMON_CONFIG_PATH,
    ConfigPaths,
)

_CONFIGS_DIR = os.path.dirname(os.path.abspath(__file__))

BAT_OVERLAY_CONFIG_PATH = f"{_CONFIGS_DIR}/battery_overlay.yaml"

BEACON_CONFIG_PATH: str = f"{_CONFIGS_DIR}/beacon.yaml"

CARD_CONFIGS_PATH: ConfigPaths = {
    "c3": (C3_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
    "battery_1": (BAT_CONFIG_PATH, FW_COMMON_CONFIG_PATH, BAT_OVERLAY_CONFIG_PATH),
    "solar_1": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_2": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_3": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "solar_4": (SOLAR_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "adcs": (ADCS_CONFIG_PATH, FW_COMMON_CONFIG_PATH),
    "gps": (GPS_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
    "star_tracker_1": (ST_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
    "dxwifi": (DXWIFI_CONFIG_PATH, SW_COMMON_CONFIG_PATH),
}
