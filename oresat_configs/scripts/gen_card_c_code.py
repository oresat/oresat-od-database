#!/usr/bin/env python3

from argparse import ArgumentParser

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


def main():
    parser = ArgumentParser("generate CANopenNode OD.[c/h] files")
    parser.add_argument(
        "-o", "--oresat", default="oresat0", help="oresat mission; oresat0 or oresat0.5"
    )
    parser.add_argument("-c", "--card", help="card name; battery, solar, or imu")
    parser.add_argument("-d", "--dir_path", default=".", help="output directory path")
    args = parser.parse_args()

    od = OD_LIST[(args.oresat.lower(), args.card)]
    write_canopennode(od, args.dir_path)


if __name__ == "__main__":
    main()
