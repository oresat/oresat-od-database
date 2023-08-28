import os
import json

from . import NodeId
from ._json_to_od import read_json_od_config, make_od, add_all_rpdo_data

_file_path = os.path.dirname(os.path.abspath(__file__))
_oresat0_json_dir = f"{_file_path}/jsons/oresat0"

_fw_core_config = read_json_od_config(f"{_oresat0_json_dir}/fw_core.json")
_sw_core_config = read_json_od_config(f"{_oresat0_json_dir}/sw_core.json")
_solar_config = read_json_od_config(f"{_oresat0_json_dir}/solar.json")
_battery_config = read_json_od_config(f"{_oresat0_json_dir}/battery.json")
_imu_config = read_json_od_config(f"{_oresat0_json_dir}/imu.json")
_c3_config = read_json_od_config(f"{_oresat0_json_dir}/c3.json")
_gps_config = read_json_od_config(f"{_oresat0_json_dir}/gps.json")
_st_config = read_json_od_config(f"{_oresat0_json_dir}/star_tracker.json")
_dxwifi_config = read_json_od_config(f"{_oresat0_json_dir}/dxwifi.json")

# make ODs for all nodes
C3_OD = make_od(_c3_config, NodeId.C3, _sw_core_config, False)
BATTERY_1_OD = make_od(_battery_config, NodeId.BATTERY_1, _fw_core_config)
SOLAR_MODULE_1_OD = make_od(_solar_config, NodeId.SOLAR_MODULE_1, _fw_core_config)
SOLAR_MODULE_2_OD = make_od(_solar_config, NodeId.SOLAR_MODULE_2, _fw_core_config)
SOLAR_MODULE_3_OD = make_od(_solar_config, NodeId.SOLAR_MODULE_3, _fw_core_config)
SOLAR_MODULE_4_OD = make_od(_solar_config, NodeId.SOLAR_MODULE_4, _fw_core_config)
GPS_OD = make_od(_gps_config, NodeId.GPS, _sw_core_config)
STAR_TRACKER_1_OD = make_od(_st_config, NodeId.STAR_TRACKER_1, _sw_core_config)
DXWIFI_OD = make_od(_dxwifi_config, NodeId.DXWIFI, _sw_core_config)
IMU_OD = make_od(_imu_config, NodeId.IMU, _fw_core_config)

# rpdo the c3 to all publish data
add_all_rpdo_data(C3_OD, BATTERY_1_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_1_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_2_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_3_OD)
add_all_rpdo_data(C3_OD, SOLAR_MODULE_4_OD)
add_all_rpdo_data(C3_OD, GPS_OD)
add_all_rpdo_data(C3_OD, STAR_TRACKER_1_OD)
add_all_rpdo_data(C3_OD, IMU_OD)
add_all_rpdo_data(C3_OD, DXWIFI_OD)

with open(f"{_oresat0_json_dir}/beacon.json", "r") as f:
    BEACON_DEF = json.load(f)
