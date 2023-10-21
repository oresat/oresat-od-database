#!/usr/bin/env python3
"""Print out a card's objects directory."""

import sys
from argparse import ArgumentParser
from typing import Any

import canopen

from .. import OD_DB, NodeId, OreSatId
from .._yaml_to_od import OD_DATA_TYPES

PRINT_OD = "print the object dictionary out to stdout"
PRINT_OD_PROG = "oresat-print-od"


def format_default(value: Any) -> str:
    """Format default value based off of python data type."""
    if isinstance(value, int) and not isinstance(value, bool):
        value = hex(value)
    elif isinstance(value, str):
        value = f'"{value}"'
    return value


def print_od(sys_args=None):
    """The print-od main"""

    if sys_args is None:
        sys_args = sys.argv[1:]

    parser = ArgumentParser(description=PRINT_OD, prog=PRINT_OD_PROG)
    parser.add_argument("oresat", default="oresat0", help="oresat mission; oresat0 or oresat0.5")
    parser.add_argument("card", help="card name; c3, gps, star_tracker_1, etc")
    args = parser.parse_args(sys_args)

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
