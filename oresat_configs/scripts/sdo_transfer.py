"""
SDO transfer script

This scipt act as CANopen master node, allowing it to read and write other
node's Object Dictionaries.
"""

import os
import sys
from argparse import ArgumentParser

import canopen

from .. import OreSatConfig, OreSatId

SDO_TRANSFER = "read or write value to a node's object dictionary via SDO transfers"
SDO_TRANSFER_PROG = "oresat-sdo-transfer"


def sdo_transfer(sys_args=None):
    """Read or write data to a node using a SDO."""

    if sys_args is None:
        sys_args = sys.argv[1:]

    parser = ArgumentParser(description=SDO_TRANSFER, prog=SDO_TRANSFER_PROG)
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
        help="oresat# (e.g.: oresat0, oresat0.5, oresat1)",
    )
    args = parser.parse_args(sys_args)

    arg_oresat = args.oresat.lower()
    if arg_oresat in ["0", "oresat0"]:
        oresat_id = OreSatId.ORESAT0
    elif arg_oresat in ["0.5", "oresat0.5"]:
        oresat_id = OreSatId.ORESAT0_5
    elif arg_oresat in ["1", "oresat1"]:
        oresat_id = OreSatId.ORESAT1
    else:
        print(f"invalid oresat mission: {args.oresat}")
        sys.exit()

    config = OreSatConfig(oresat_id)

    if args.value.startswith("file:"):
        if not os.path.isfile(args.value[5:]):
            print(f"file does not exist {args.value[5:]}")
            sys.exit()

    node_name = args.node.lower()
    od = config.od_db[node_name]

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
