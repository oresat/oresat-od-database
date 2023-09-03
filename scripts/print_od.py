#!/usr/bin/env python3
"""Print out a card's objects directory."""

import os
import sys
from argparse import ArgumentParser
from typing import Any

_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{_FILE_PATH}/..")

import canopen
from oresat_configs import NodeId, oresat0, oresat0_5
from oresat_configs._json_to_od import OD_DATA_TYPES


def format_default(raw: Any) -> str:
    """Format default value based off of python data type."""
    if isinstance(raw, int) and not isinstance(raw, bool):
        raw = hex(raw)
    elif isinstance(value, str):
        raw = f'"{raw}"'
    return raw


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

    inverted_od_data_types = {}
    for key in OD_DATA_TYPES:
        inverted_od_data_types[OD_DATA_TYPES[key]] = key

    od = ods[NodeId[args.card.upper()]]
    for i in od:
        if isinstance(od[i], canopen.objectdictionary.Variable):
            data_type = inverted_od_data_types[od[i].data_type]
            value = format_default(od[i].default)
            print(f"0x{i:04X}: {od[i].name} - {data_type} - {value}")
        else:
            print(f"0x{i:04X}: {od[i].name}")
            for j in od[i]:
                data_type = inverted_od_data_types[od[i][j].data_type]
                value = format_default(od[i][j].default)
                print(f"  0x{i:04X} 0x{j:02X}: {od[i][j].name} - {data_type} - {value}")
