import os

from .._json_to_od import read_json_od_config

_JSON_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/jsons"
FW_COMMON_CONFIG = read_json_od_config(f"{_JSON_DIR}/fw_common.json")
SW_COMMON_CONFIG = read_json_od_config(f"{_JSON_DIR}/sw_common.json")
C3_CONFIG = read_json_od_config(f"{_JSON_DIR}/c3.json")
BAT_CONFIG = read_json_od_config(f"{_JSON_DIR}/battery.json")
SOLAR_CONFIG = read_json_od_config(f"{_JSON_DIR}/solar.json")
IMU_CONFIG = read_json_od_config(f"{_JSON_DIR}/imu.json")
RW_CONFIG = read_json_od_config(f"{_JSON_DIR}/reaction_wheel.json")
GPS_CONFIG = read_json_od_config(f"{_JSON_DIR}/gps.json")
ST_CONFIG = read_json_od_config(f"{_JSON_DIR}/star_tracker.json")
DXWIFI_CONFIG = read_json_od_config(f"{_JSON_DIR}/dxwifi.json")
CFC_CONFIG = read_json_od_config(f"{_JSON_DIR}/cfc.json")
