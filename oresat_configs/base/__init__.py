"""OreSat od base configs."""

import os

from .._yaml_to_od import read_yaml_od_config

_CONFIGS_DIR = os.path.dirname(os.path.abspath(__file__))
FW_COMMON_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/fw_common.yaml")
SW_COMMON_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/sw_common.yaml")
C3_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/c3.yaml")
BAT_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/battery.yaml")
SOLAR_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/solar.yaml")
IMU_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/imu.yaml")
RW_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/reaction_wheel.yaml")
GPS_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/gps.yaml")
ST_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/star_tracker.yaml")
DXWIFI_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/dxwifi.yaml")
CFC_CONFIG = read_yaml_od_config(f"{_CONFIGS_DIR}/cfc.yaml")
