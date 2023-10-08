#!/usr/bin/env python3
"""
SDO transfer script

This scipt act as CANopen master node, allowing it to read and write other
node's Object Dictionaries.
"""

import os
import sys
from argparse import ArgumentParser

import canopen

from oresat_od_db import OD_DB, NodeId, OreSatId


def main():
    """Read or write data to a node using a SDO."""

    parser = ArgumentParser(
        description="read or write value to a node's object dictionary",
    )
    parser.add_argument("bus", metavar="BUS", help="CAN bus to use (e.g., can0, vcan0)")
    parser.add_argument("node", metavar="NODE", help="device node name (e.g. gps, solar_module_1)")
    parser.add_argument("mode", metavar="MODE", help="r[ead] or w[rite] (e.g. r, read, w, write)")
    parser.add_argument("index", metavar="INDEX", help="object dictionary index")
    parser.add_argument("subindex", metavar="SUBINDEX", help='object dictionary subindex or "none"')
    parser.add_argument(
        "value",
        metavar="VALUE",
        nargs="?",
        default="",
        help="data to write or for only octet/domain data types a path to a file "
        "(e.g. file:data.bin)",
    )
    parser.add_argument(
        "-o",
        "--oresat",
        metavar="ORESAT",
        default="oresat0.5",
        help="oresat# (e.g.: oresat0,  oresat0.5)",
    )
    args = parser.parse_args()

    if args.oresat == "oresat0":
        od_db = OD_DB[OreSatId.ORESAT0]
    elif args.oresat == "oresat0.5":
        od_db = OD_DB[OreSatId.ORESAT0_5]
    else:
        print(f"invalid oresat mission {args.oresat}")
        sys.exit()

    if args.value.startswith("file:"):
        if not os.path.isfile(args.value[5:]):
            print(f"file does not exist {args.value[5:]}")
            sys.exit()

    node_id = NodeId[args.node.upper()]
    od = od_db[node_id]

    # connect to CAN network
    network = canopen.Network()
    node = canopen.RemoteNode(od.node_id, od)
    network.add_node(node)
    network.connect(bustype="socketcan", channel=args.bus)

    # validate object exist and make sdo obj
    try:
        if args.subindex == "none":
            obj = od[args.index]
            sdo = node.sdo[args.index]
        else:
            obj = od[args.index][args.subindex]
            sdo = node.sdo[args.index][args.subindex]
    except KeyError as e:
        print(e)
        sys.exit()

    binary_type = [canopen.objectdictionary.OCTET_STRING, canopen.objectdictionary.DOMAIN]

    # send SDO
    try:
        if args.mode in ["r", "read"]:
            if obj.data_type == binary_type:
                with open(args.value[5:], "wb") as f:
                    f.write(sdo.raw)
                    value = f"binary data written to {args.value[5:]}"
            else:
                value = sdo.phys
            print(value)
        elif args.mode in ["w", "write"]:
            # convert string input to correct data type
            if obj.data_type in canopen.objectdictionary.INTEGER_TYPES:
                value = int(args.value, 16) if args.value.startswith("0x") else int(args.value)
            elif obj.data_type in canopen.objectdictionary.FLOAT_TYPES:
                value = float(args.value)
            elif obj.data_type == canopen.objectdictionary.VISIBLE_STRING:
                value = args.value
            elif obj.data_type in binary_type:  # read in binary data from file
                with open(args.value[5:], "rb") as f:
                    value = f.read()

            if obj.data_type == binary_type:
                sdo.raw = value
            else:
                sdo.phys = value
        else:
            print('invalid mode\nmust be "r", "read", "w", or "write"')
    except (canopen.SdoAbortedError, AttributeError, FileNotFoundError) as e:
        print(e)

    network.disconnect()


if __name__ == "__main__":
    main()
