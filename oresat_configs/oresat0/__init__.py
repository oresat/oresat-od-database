"""OreSat0 object dictionary and beacon constants."""

import os

import yaml

from .._yaml_to_od import read_yaml_od_config
from ..base import (
    BAT_CONFIG,
    C3_CONFIG,
    DXWIFI_CONFIG,
    FW_COMMON_CONFIG,
    GPS_CONFIG,
    IMU_CONFIG,
    SOLAR_CONFIG,
    ST_CONFIG,
    SW_COMMON_CONFIG,
)
from ..constants import NodeId

_CONFIGS_DIR = os.path.dirname(os.path.abspath(__file__))
BAT_CONFIG_OVERLAY = read_yaml_od_config(f"{_CONFIGS_DIR}/battery_overlay.yaml")

with open(f"{_CONFIGS_DIR}/beacon.yaml", "r") as f:
    ORESAT0_BEACON_CONFIG = yaml.safe_load(f)

ORESAT0_CARD_CONFIGS = {
    NodeId.C3: (C3_CONFIG, SW_COMMON_CONFIG),
    NodeId.BATTERY_1: (BAT_CONFIG, FW_COMMON_CONFIG, BAT_CONFIG_OVERLAY),
    NodeId.SOLAR_MODULE_1: (SOLAR_CONFIG, FW_COMMON_CONFIG),
    NodeId.SOLAR_MODULE_2: (SOLAR_CONFIG, FW_COMMON_CONFIG),
    NodeId.SOLAR_MODULE_3: (SOLAR_CONFIG, FW_COMMON_CONFIG),
    NodeId.SOLAR_MODULE_4: (SOLAR_CONFIG, FW_COMMON_CONFIG),
    NodeId.IMU: (IMU_CONFIG, FW_COMMON_CONFIG),
    NodeId.GPS: (GPS_CONFIG, SW_COMMON_CONFIG),
    NodeId.STAR_TRACKER_1: (ST_CONFIG, SW_COMMON_CONFIG),
    NodeId.DXWIFI: (DXWIFI_CONFIG, SW_COMMON_CONFIG),
}
