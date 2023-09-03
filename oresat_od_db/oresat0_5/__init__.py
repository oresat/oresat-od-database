"""OreSat0.5 object dictionary and beacon globals."""

import os
import json

from .. import NodeId, OreSatId
from .._json_to_od import read_json_od_config, gen_ods

ORESAT_ID = OreSatId.ORESAT0_5

_JSON_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/jsons"
_FW_CORE_CONFIG = read_json_od_config(f"{_JSON_DIR}/fw_core.json")
_SW_CORE_CONFIG = read_json_od_config(f"{_JSON_DIR}/sw_core.json")
_C3_CONFIG = read_json_od_config(f"{_JSON_DIR}/c3.json")
_BAT_CONFIG = read_json_od_config(f"{_JSON_DIR}/battery.json")
_SOLAR_CONFIG = read_json_od_config(f"{_JSON_DIR}/solar.json")
_IMU_CONFIG = read_json_od_config(f"{_JSON_DIR}/imu.json")
_RW_CONFIG = read_json_od_config(f"{_JSON_DIR}/reaction_wheel.json")
_GPS_CONFIG = read_json_od_config(f"{_JSON_DIR}/gps.json")
_ST_CONFIG = read_json_od_config(f"{_JSON_DIR}/star_tracker.json")
_DXWIFI_CONFIG = read_json_od_config(f"{_JSON_DIR}/dxwifi.json")
_CFC_CONFIG = read_json_od_config(f"{_JSON_DIR}/cfc.json")


with open(f"{_JSON_DIR}/beacon.json", "r") as f:
    BEACON_DEF = json.load(f)


OD_DB = gen_ods(
    ORESAT_ID,
    BEACON_DEF,
    {
        NodeId.C3: (_C3_CONFIG, _SW_CORE_CONFIG),
        NodeId.BATTERY_1: (_BAT_CONFIG, _FW_CORE_CONFIG),
        NodeId.SOLAR_MODULE_1: (_SOLAR_CONFIG, _FW_CORE_CONFIG),
        NodeId.SOLAR_MODULE_2: (_SOLAR_CONFIG, _FW_CORE_CONFIG),
        NodeId.SOLAR_MODULE_3: (_SOLAR_CONFIG, _FW_CORE_CONFIG),
        NodeId.SOLAR_MODULE_4: (_SOLAR_CONFIG, _FW_CORE_CONFIG),
        NodeId.SOLAR_MODULE_5: (_SOLAR_CONFIG, _FW_CORE_CONFIG),
        NodeId.SOLAR_MODULE_6: (_SOLAR_CONFIG, _FW_CORE_CONFIG),
        NodeId.IMU: (_IMU_CONFIG, _FW_CORE_CONFIG),
        NodeId.REACTION_WHEEL_1: (_RW_CONFIG, _FW_CORE_CONFIG),
        NodeId.REACTION_WHEEL_2: (_RW_CONFIG, _FW_CORE_CONFIG),
        NodeId.REACTION_WHEEL_3: (_RW_CONFIG, _FW_CORE_CONFIG),
        NodeId.REACTION_WHEEL_4: (_RW_CONFIG, _FW_CORE_CONFIG),
        NodeId.GPS: (_GPS_CONFIG, _SW_CORE_CONFIG),
        NodeId.STAR_TRACKER_1: (_ST_CONFIG, _SW_CORE_CONFIG),
        NodeId.DXWIFI: (_DXWIFI_CONFIG, _SW_CORE_CONFIG),
        NodeId.CFC: (_CFC_CONFIG, _SW_CORE_CONFIG),
    },
)

# direct access to ODs
C3_OD = OD_DB[NodeId.C3]
BATTERY_1_OD = OD_DB[NodeId.BATTERY_1]
SOLAR_MODULE_1_OD = OD_DB[NodeId.SOLAR_MODULE_1]
SOLAR_MODULE_2_OD = OD_DB[NodeId.SOLAR_MODULE_2]
SOLAR_MODULE_3_OD = OD_DB[NodeId.SOLAR_MODULE_3]
SOLAR_MODULE_4_OD = OD_DB[NodeId.SOLAR_MODULE_4]
SOLAR_MODULE_5_OD = OD_DB[NodeId.SOLAR_MODULE_5]
SOLAR_MODULE_6_OD = OD_DB[NodeId.SOLAR_MODULE_6]
IMU_OD = OD_DB[NodeId.IMU]
REACTION_WHEEL_1_OD = OD_DB[NodeId.REACTION_WHEEL_1]
REACTION_WHEEL_2_OD = OD_DB[NodeId.REACTION_WHEEL_2]
REACTION_WHEEL_3_OD = OD_DB[NodeId.REACTION_WHEEL_3]
REACTION_WHEEL_4_OD = OD_DB[NodeId.REACTION_WHEEL_4]
GPS_OD = OD_DB[NodeId.GPS]
STAR_TRACKER_1_OD = OD_DB[NodeId.STAR_TRACKER_1]
DXWIFI_OD = OD_DB[NodeId.DXWIFI]
CFC_OD = OD_DB[NodeId.CFC]
