#!/usr/bin/env python3
"""Print out a card's objects directory."""

import os
import sys
from argparse import ArgumentParser
from typing import Any

_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{_FILE_PATH}/..")

import canopen

from oresat_od_db import OD_DB, NodeId, OreSatId
from oresat_od_db._yaml_to_od import OD_DATA_TYPES


def format_default(value: Any) -> str:
    """Format default value based off of python data type."""
    if isinstance(value, int) and not isinstance(value, bool):
        value = hex(value)
    elif isinstance(value, str):
        value = f'"{value}"'
    return value


def main():
    """The main"""

    parser = ArgumentParser()
    parser.add_argument("oresat", default="oresat0", help="oresat mission; oresat0 or oresat0.5")
    parser.add_argument("card", help="card name; c3, gps, star_tracker_1, etc")
    args = parser.parse_args()

    if args.oresat == "oresat0":
        od_db = OD_DB[OreSatId.ORESAT0]
    elif args.oresat == "oresat0.5":
        od_db = OD_DB[OreSatId.ORESAT0_5]
    elif args.oresat == "oresat1":
        od_db = OD_DB[OreSatId.ORESAT1]
    else:
        print(f"invalid oresat mission {args.oresat}")
        sys.exit()

    if args.card is None:
        print("card not set")
        sys.exit()

    inverted_od_data_types = {}
    for key in OD_DATA_TYPES:
        inverted_od_data_types[OD_DATA_TYPES[key]] = key

    od = od_db[NodeId[args.card.upper()]]
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


if __name__ == "__main__":
    main()
