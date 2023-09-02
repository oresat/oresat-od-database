#!/usr/bin/env python3
"""Print out a card's objects directory."""

import os
import sys
from argparse import ArgumentParser

_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{_FILE_PATH}/..")

import canopen
from oresat_configs import oresat0, oresat0_5
from oresat_configs._json_to_od import OD_DATA_TYPES

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("oresat", default="oresat0", help="oresat mission; oresat0 or oresat0.5")
    parser.add_argument("card", help="card name; c3, gps, star_tracker_1, etc")
    args = parser.parse_args()

    if args.oresat == "oresat0":
        ods = oresat0.ALL_ODS
    elif args.oresat == "oresat0.5":
        ods = oresat0_5.ALL_ODS
    else:
        print(f"invalid oresat mission {args.oresat}")
        sys.exit()

    if args.card is None:
        print("card not set")
        sys.exit()

    od = ods[args.card.lower()]

    for i in od:
        print(f"0x{i:04X}: {od[i].name}")
        if not isinstance(od[i], canopen.objectdictionary.Variable):
            for j in od[i]:
                data_type = od[i][j].data_type
                data_type_str = list(OD_DATA_TYPES.keys())[
                    list(OD_DATA_TYPES.values()).index(data_type)
                ]
                value = od[i][j].default
                if isinstance(value, int) and not isinstance(value, bool):
                    value = hex(value)
                elif isinstance(value, str):
                    value = f'"{value}"'
                print(f"  0x{i:04X} 0x{j:02X}: {od[i][j].name} - {data_type_str} - {value}")
