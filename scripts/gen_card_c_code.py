#!/usr/bin/env python3

import os
import sys
from argparse import ArgumentParser

_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{_FILE_PATH}/..")

from oresat_configs import oresat0, oresat0_5
from oresat_configs._write_canopennode import write_canopennode


OD_LIST = {
    ("oresat0", "c3"): oresat0.C3_OD,
    ("oresat0", "battery"): oresat0.BATTERY_1_OD,
    ("oresat0", "solar"): oresat0.SOLAR_MODULE_1_OD,
    ("oresat0", "imu"): oresat0.IMU_OD,
    ("oresat0.5", "battery"): oresat0_5.BATTERY_1_OD,
    ("oresat0.5", "solar"): oresat0_5.SOLAR_MODULE_1_OD,
    ("oresat0.5", "imu"): oresat0_5.IMU_OD,
    ("oresat0.5", "reaction_wheel"): oresat0_5.REACTION_WHEEL_1_OD,
}


if __name__ == "__main__":
    parser = ArgumentParser("generate CANopenNode OD.[c/h] files")
    parser.add_argument("oresat", help="oresat mission; oresat0 or oresat0.5")
    parser.add_argument("card", help="card name; c3, battery, solar, imu, or reaction_wheel")
    parser.add_argument(
        "-d", "--dir_path", default=".", help='output directory path, default: "."'
    )
    args = parser.parse_args()

    if (args.oresat.lower(), args.card) not in OD_LIST:
        print("invalid oresat and/or card")
        sys.exit()

    od = OD_LIST[(args.oresat.lower(), args.card)]
    write_canopennode(od, args.dir_path)
