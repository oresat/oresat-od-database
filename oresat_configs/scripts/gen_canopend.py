import os
from argparse import ArgumentParser, Namespace
from typing import Any, Optional

import canopen

from oresat_configs import Mission, OreSatConfig

GEN_CANOPEND = "generate od file for OreSat Linux apps"

DATATYPE_NAMES = {
    0x1: "BOOL",
    0x2: "INT8",
    0x3: "INT16",
    0x4: "INT32",
    0x5: "UINT8",
    0x6: "UINT16",
    0x7: "UINT32",
    0x8: "FLOAT32",
    0x9: "STR",
    0xA: "BYTES",
    0xF: "DOMAIN",
    0x11: "FLOAT64",
    0x15: "INT64",
    0x1B: "UINT64",
}


def build_parser(parser: ArgumentParser) -> ArgumentParser:
    parser.description = GEN_CANOPEND
    parser.add_argument(
        "--oresat",
        default=Mission.default().arg,
        choices=[m.arg for m in Mission],
        type=lambda x: x.lower().removeprefix("oresat"),
        help="Oresat Mission. (Default: %(default)s)",
    )
    parser.add_argument("card", help="card name; all, c3, gps, star_tracker_1, etc")
    parser.add_argument("-d", "--dir-path", default=".", help='directory path; defautl "."')
    return parser


def register_subparser(subparsers: Any):
    parser = build_parser(subparsers.add_parser("canopend", help=GEN_CANOPEND))
    parser.set_defaults(func=gen_canopend)


def write_canopend(card: str, od: canopen.ObjectDictionary, dir_path: str = "."):
    enums = {}
    bitfields = {}
    entries = {}
    tpdos = []

    def snake_to_camel(name):
        return "".join(word.title() for word in name.split("_"))

    node_name = snake_to_camel(card)

    for index in sorted(od.indices):
        obj = od[index]

        if 0x1800 <= index < 0x1A00:
            tpdos.append(index - 0x1800 + 1)

        if index < 0x4000:
            continue

        base_name = ""
        if 0x4000 > index > 0x5000:
            base_name = card + "_"

        if isinstance(obj, canopen.objectdictionary.Variable):
            name = base_name + obj.name
            if obj.value_descriptions:
                enums[name] = obj.value_descriptions
            if obj.bit_definitions:
                bitfields[name] = obj.bit_definitions
            entries[name] = obj
        else:
            for sub_obj in obj.subindices.values():
                if sub_obj.subindex == 0:
                    continue

                name = f"{base_name}{obj.name}_{sub_obj.name}"

                if sub_obj.value_descriptions:
                    enums[name] = sub_obj.value_descriptions
                if sub_obj.bit_definitions:
                    bitfields[name] = sub_obj.bit_definitions
                entries[name] = sub_obj

    lines = []

    if enums:
        lines.append("from enum import Enum\n\n")

    line = "from oresat_libcanopend import DataType, Entry"
    if bitfields:
        line += ", EntryBitField"
    line += "\n"
    lines.append(line)

    for e_name, values in enums.items():
        lines.append("\n")
        lines.append("\n")
        c_name = snake_to_camel(e_name)
        lines.append(f"class {c_name}(Enum):\n")
        for value, name in values.items():
            lines.append(f"    {name.upper()} = {value}\n")

    for b_name, values in bitfields.items():
        lines.append("\n")
        lines.append("\n")
        c_name = snake_to_camel(b_name)
        lines.append(f"class {c_name}BitField(EntryBitField):\n")
        for name, value in values.items():
            lines.append(f"    {name.upper()} = {value}\n")

    lines.append("\n")
    lines.append("\n")
    lines.append(f"class {node_name}Entry(Entry):\n")
    for name, obj in entries.items():
        dt = DATATYPE_NAMES[obj.data_type]
        c_name = snake_to_camel(name)
        e_enum = c_name if obj.value_descriptions else "None"
        bitfield = f"{c_name}BitField" if obj.bit_definitions else "None"
        line = f"    {name.upper()} = 0x{obj.index:X}, 0x{obj.subindex:X}, DataType.{dt}"
        default = obj.value
        if isinstance(default, str):
            default = f'"{default}"'
        line += f", {default}"
        if not (obj.min is None or obj.max is None or e_enum is None or bitfield is None):
            line += f", {obj.min}, {obj.max}, {e_enum}, {bitfield}"
        line += "\n"
        lines.append(line)

    lines.append("\n")
    lines.append("\n")
    lines.append(f"class {node_name}Tpdo(Enum):\n")
    for i in range(len(tpdos)):
        lines.append(f"    TPDO_{tpdos[i]} = {i}\n")

    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    output_file = os.path.join(dir_path, "od.py")
    with open(output_file, "w") as f:
        f.writelines(lines)


def gen_canopend(args: Optional[Namespace] = None):
    """Gen canopend main."""
    if args is None:
        args = build_parser(ArgumentParser()).parse_args()

    config = OreSatConfig(args.oresat)
    od = config.od_db[args.card.lower()]
    write_canopend(args.card.lower(), od, args.dir_path)
