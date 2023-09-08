"""OreSat0 object dictionary and beacon globals."""

import json
import os

from .. import NodeId, OreSatId
from .._json_to_od import gen_od_db, read_json_od_config

ORESAT_ID = OreSatId.ORESAT0

_JSON_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/jsons"
_FW_COMMON_CONFIG = read_json_od_config(f"{_JSON_DIR}/fw_common.json")
_SW_COMMON_CONFIG = read_json_od_config(f"{_JSON_DIR}/sw_common.json")
_C3_CONFIG = read_json_od_config(f"{_JSON_DIR}/c3.json")
_BAT_CONFIG = read_json_od_config(f"{_JSON_DIR}/battery.json")
_SOLAR_CONFIG = read_json_od_config(f"{_JSON_DIR}/solar.json")
_IMU_CONFIG = read_json_od_config(f"{_JSON_DIR}/imu.json")
_GPS_CONFIG = read_json_od_config(f"{_JSON_DIR}/gps.json")
_ST_CONFIG = read_json_od_config(f"{_JSON_DIR}/star_tracker.json")
_DXWIFI_CONFIG = read_json_od_config(f"{_JSON_DIR}/dxwifi.json")


with open(f"{_JSON_DIR}/beacon.json", "r") as f:
    BEACON_DEF = json.load(f)


OD_DB = gen_od_db(
    ORESAT_ID,
    BEACON_DEF,
    {
        NodeId.C3: (_C3_CONFIG, _FW_COMMON_CONFIG),
        NodeId.BATTERY_1: (_BAT_CONFIG, _FW_COMMON_CONFIG),
        NodeId.SOLAR_MODULE_1: (_SOLAR_CONFIG, _FW_COMMON_CONFIG),
        NodeId.SOLAR_MODULE_2: (_SOLAR_CONFIG, _FW_COMMON_CONFIG),
        NodeId.SOLAR_MODULE_3: (_SOLAR_CONFIG, _FW_COMMON_CONFIG),
        NodeId.SOLAR_MODULE_4: (_SOLAR_CONFIG, _FW_COMMON_CONFIG),
        NodeId.IMU: (_IMU_CONFIG, _FW_COMMON_CONFIG),
        NodeId.GPS: (_GPS_CONFIG, _SW_COMMON_CONFIG),
        NodeId.STAR_TRACKER_1: (_ST_CONFIG, _SW_COMMON_CONFIG),
        NodeId.DXWIFI: (_DXWIFI_CONFIG, _SW_COMMON_CONFIG),
    },
)

# direct access to ODs
C3_OD = OD_DB[NodeId.C3]
BATTERY_1_OD = OD_DB[NodeId.BATTERY_1]
SOLAR_MODULE_1_OD = OD_DB[NodeId.SOLAR_MODULE_1]
SOLAR_MODULE_2_OD = OD_DB[NodeId.SOLAR_MODULE_2]
SOLAR_MODULE_3_OD = OD_DB[NodeId.SOLAR_MODULE_3]
SOLAR_MODULE_4_OD = OD_DB[NodeId.SOLAR_MODULE_4]
IMU_OD = OD_DB[NodeId.IMU]
GPS_OD = OD_DB[NodeId.GPS]
STAR_TRACKER_1_OD = OD_DB[NodeId.STAR_TRACKER_1]
DXWIFI_OD = OD_DB[NodeId.DXWIFI]
