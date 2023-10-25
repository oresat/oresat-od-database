#!/usr/bin/env python3

import os
import sys

_FILE_PATH = os.path.dirname(os.path.abspath(__file__ + "/../.."))
sys.path.insert(0, _FILE_PATH)
_FILE_PATH = os.path.dirname(os.path.abspath(__file__ + "/.."))

import canopen

from oresat_configs import BEACON_DEF_DB, OreSatId

OD_DATA_TYPES = {
    canopen.objectdictionary.BOOLEAN: "bool",
    canopen.objectdictionary.INTEGER8: "int8",
    canopen.objectdictionary.INTEGER16: "int16",
    canopen.objectdictionary.INTEGER32: "int32",
    canopen.objectdictionary.INTEGER64: "int64",
    canopen.objectdictionary.UNSIGNED8: "uint8",
    canopen.objectdictionary.UNSIGNED16: "uint16",
    canopen.objectdictionary.UNSIGNED32: "uint32",
    canopen.objectdictionary.UNSIGNED64: "uint64",
    canopen.objectdictionary.REAL32: "float32",
    canopen.objectdictionary.REAL64: "float64",
    canopen.objectdictionary.VISIBLE_STRING: "str",
    canopen.objectdictionary.OCTET_STRING: "octect_str",
    canopen.objectdictionary.DOMAIN: "domain",
}


def gen_beacon_rst(beacon_def: list, oresat: str, file_path: str):
    """Genetate a rst file for a beacon definition."""

    title = f"{oresat} Beacon Definition"
    lines = [
        f"{title}\n",
        f'{"=" * len(title)}\n',
        "\n",
        ".. csv-table::\n",
        '   :header: "Offset", "Card", "Data Name", "Data Type", "Size", "Description"\n',
        "\n",
    ]

    offset = 0
    size = 16
    desc = "\nax.25 packet header\n"
    desc = desc.replace("\n", "\n   ")
    lines.append(f'   "{offset}", "c3", "ax25_header", "octect_str", "{size}", "{desc}"\n')
    offset += size

    for obj in beacon_def:
        if isinstance(obj.parent, canopen.ObjectDictionary):
            index_name = obj.name
            subindex_name = ""
        else:
            index_name = obj.parent.name
            subindex_name = obj.name

        if obj.index < 0x5000:
            card = "c3"
            name = index_name
            name += "_" + subindex_name if subindex_name else ""
        else:
            card = index_name
            name = subindex_name

        if obj.data_type == canopen.objectdictionary.VISIBLE_STRING:
            size = len(obj.default)
        else:
            size = len(obj.encode_raw(obj.default))

        data_type = OD_DATA_TYPES[obj.data_type]
        desc = "\n" + obj.description + "\n"
        desc = desc.replace("\n", "\n   ")

        lines.append(f'   "{offset}", "{card}", "{name}", "{data_type}", "{size}", "{desc}"\n')
        offset += size

    size = 4
    desc = "\npacket checksum\n"
    desc = desc.replace("\n", "\n   ")
    lines.append(f'   "{offset}", "c3", "crc32", "uint32", "{size}", "{desc}"\n')
    offset += size

    lines.append("\n")
    lines.append(f"Total length: {offset}\n")

    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with open(file_path, "w") as f:
        f.writelines(lines)


def gen_all():
    file_path = _FILE_PATH + "/" + "gen"
    gen_beacon_rst(BEACON_DEF_DB[OreSatId.ORESAT0], "OreSat0", f"{file_path}/oresat0_beacon.rst")
    gen_beacon_rst(
        BEACON_DEF_DB[OreSatId.ORESAT0_5], "OreSat0.5", f"{file_path}/oresat0_5_beacon.rst"
    )
    gen_beacon_rst(BEACON_DEF_DB[OreSatId.ORESAT1], "OreSat1", f"{file_path}/oresat1_beacon.rst")
