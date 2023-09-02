"""OreSat0.5 object dictionary and beacon globals."""

import os
import json

from .. import NodeId, OreSatId
from .._json_to_od import read_json_od_config, make_od, add_all_rpdo_data

_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
_JSON_DIR = f"{_FILE_PATH}/jsons"

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

# make ODs for all nodes
C3_OD = make_od(NodeId.C3, _C3_CONFIG, _SW_CORE_CONFIG, False)
BATTERY_1_OD = make_od(NodeId.BATTERY_1, _BAT_CONFIG, _FW_CORE_CONFIG)
SOLAR_MODULE_1_OD = make_od(NodeId.SOLAR_MODULE_1, _SOLAR_CONFIG, _FW_CORE_CONFIG)
SOLAR_MODULE_2_OD = make_od(NodeId.SOLAR_MODULE_2, _SOLAR_CONFIG, _FW_CORE_CONFIG)
SOLAR_MODULE_3_OD = make_od(NodeId.SOLAR_MODULE_3, _SOLAR_CONFIG, _FW_CORE_CONFIG)
SOLAR_MODULE_4_OD = make_od(NodeId.SOLAR_MODULE_4, _SOLAR_CONFIG, _FW_CORE_CONFIG)
SOLAR_MODULE_5_OD = make_od(NodeId.SOLAR_MODULE_5, _SOLAR_CONFIG, _FW_CORE_CONFIG)
SOLAR_MODULE_6_OD = make_od(NodeId.SOLAR_MODULE_6, _SOLAR_CONFIG, _FW_CORE_CONFIG)
IMU_OD = make_od(NodeId.IMU, _IMU_CONFIG, _FW_CORE_CONFIG)
REACTION_WHEEL_1_OD = make_od(NodeId.REACTION_WHEEL_1, _RW_CONFIG, _FW_CORE_CONFIG)
REACTION_WHEEL_2_OD = make_od(NodeId.REACTION_WHEEL_2, _RW_CONFIG, _FW_CORE_CONFIG)
REACTION_WHEEL_3_OD = make_od(NodeId.REACTION_WHEEL_3, _RW_CONFIG, _FW_CORE_CONFIG)
REACTION_WHEEL_4_OD = make_od(NodeId.REACTION_WHEEL_4, _RW_CONFIG, _FW_CORE_CONFIG)
GPS_OD = make_od(NodeId.GPS, _GPS_CONFIG, _SW_CORE_CONFIG)
STAR_TRACKER_1_OD = make_od(NodeId.STAR_TRACKER_1, _ST_CONFIG, _SW_CORE_CONFIG)
DXWIFI_OD = make_od(NodeId.DXWIFI, _DXWIFI_CONFIG, _SW_CORE_CONFIG)
CFC_OD = make_od(NodeId.CFC, _CFC_CONFIG, _SW_CORE_CONFIG)

# subscribe the c3 to all tpdo data
add_all_rpdo_data(C3_OD, BATTERY_1_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_1_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_2_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_3_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_4_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_5_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_6_OD)
add_all_rpdo_data(C3_OD, GPS_OD)
add_all_rpdo_data(C3_OD, STAR_TRACKER_1_OD)
add_all_rpdo_data(C3_OD, IMU_OD)
add_all_rpdo_data(C3_OD, REACTION_WHEEL_1_OD)
add_all_rpdo_data(C3_OD, REACTION_WHEEL_2_OD)
add_all_rpdo_data(C3_OD, REACTION_WHEEL_3_OD)
add_all_rpdo_data(C3_OD, REACTION_WHEEL_4_OD)
add_all_rpdo_data(C3_OD, CFC_OD)
add_all_rpdo_data(C3_OD, DXWIFI_OD)

with open(f"{_JSON_DIR}/beacon.json", "r") as f:
    BEACON_DEF = json.load(f)

# C3 defaults
C3_OD["card_data"]["beacon_revision"].default = BEACON_DEF["revision"]
C3_OD["card_data"]["beacon_revision"].value = BEACON_DEF["revision"]
C3_OD["card_data"]["satellite_id"].default = OreSatId.ORESAT0_5.value
C3_OD["card_data"]["satellite_id"].value = OreSatId.ORESAT0_5.value


ALL_ODS = {
    "c3": C3_OD,
    "battery_1": BATTERY_1_OD,
    "solar_module_1": SOLAR_MODULE_1_OD,
    "solar_module_2": SOLAR_MODULE_2_OD,
    "solar_module_3": SOLAR_MODULE_3_OD,
    "solar_module_4": SOLAR_MODULE_4_OD,
    "solar_module_5": SOLAR_MODULE_5_OD,
    "solar_module_6": SOLAR_MODULE_6_OD,
    "gps": GPS_OD,
    "star_tracker": STAR_TRACKER_1_OD,
    "cfc": CFC_OD,
    "dxwifi": DXWIFI_OD,
    "reaction_wheel_1": REACTION_WHEEL_1_OD,
    "reaction_wheel_2": REACTION_WHEEL_2_OD,
    "reaction_wheel_3": REACTION_WHEEL_3_OD,
    "reaction_wheel_4": REACTION_WHEEL_4_OD,
    "imu": IMU_OD,
}

NON_C3_ODS = {
    "battery_1": BATTERY_1_OD,
    "solar_module_1": SOLAR_MODULE_1_OD,
    "solar_module_2": SOLAR_MODULE_2_OD,
    "solar_module_3": SOLAR_MODULE_3_OD,
    "solar_module_4": SOLAR_MODULE_4_OD,
    "solar_module_5": SOLAR_MODULE_5_OD,
    "solar_module_6": SOLAR_MODULE_6_OD,
    "gps": GPS_OD,
    "star_tracker": STAR_TRACKER_1_OD,
    "cfc": CFC_OD,
    "dxwifi": DXWIFI_OD,
    "reaction_wheel_1": REACTION_WHEEL_1_OD,
    "reaction_wheel_2": REACTION_WHEEL_2_OD,
    "reaction_wheel_3": REACTION_WHEEL_3_OD,
    "reaction_wheel_4": REACTION_WHEEL_4_OD,
    "imu": IMU_OD,
}
