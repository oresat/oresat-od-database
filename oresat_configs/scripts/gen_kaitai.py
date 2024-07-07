"""Generate KaiTai for the beacon."""

from argparse import ArgumentParser, Namespace
from yaml import dump
from datetime import datetime
from typing import Any, Optional

import canopen

from .. import Consts, OreSatConfig

GEN_KAITAI = "generate beacon kaitai configuration"


def build_parser(parser: ArgumentParser) -> ArgumentParser:
    """Configures an ArgumentParser suitable for this script.

    The given parser may be standalone or it may be used as a subcommand in another ArgumentParser.
    """
    parser.description = GEN_KAITAI
    parser.add_argument(
        "--oresat",
        default=Consts.default().arg,
        choices=[m.arg for m in Consts],
        type=lambda x: x.lower().removeprefix("oresat"),
        help="oresat mission, defaults to %(default)s",
    )
    parser.add_argument("-d", "--dir-path", default=".", help='directory path; defautl "."')
    return parser


def register_subparser(subparsers: Any) -> None:
    """Registers an ArgumentParser as a subcommand of another parser.

    Intended to be called by __main__.py for each script. Given the output of add_subparsers(),
    (which I think is a subparser group, but is technically unspecified) this function should
    create its own ArgumentParser via add_parser(). It must also set_default() the func argument
    to designate the entry point into this script.
    See https://docs.python.org/3/library/argparse.html#sub-commands, especially the end of that
    section, for more.
    """
    parser = build_parser(subparsers.add_parser("xtce", help=GEN_KAITAI))
    parser.set_defaults(func=GEN_KAITAI)


CANOPEN_TO_KAITAI_DT = {
    canopen.objectdictionary.BOOLEAN: "s",
    canopen.objectdictionary.INTEGER8: "int8",
    canopen.objectdictionary.INTEGER16: "i1",
    canopen.objectdictionary.INTEGER32: "i2",
    canopen.objectdictionary.INTEGER64: "i3",
    canopen.objectdictionary.UNSIGNED8: "u1",
    canopen.objectdictionary.UNSIGNED16: "u2",
    canopen.objectdictionary.UNSIGNED32: "u3",
    canopen.objectdictionary.UNSIGNED64: "u4",
    canopen.objectdictionary.VISIBLE_STRING: "str",
    canopen.objectdictionary.REAL32: "float",
    canopen.objectdictionary.REAL64: "double",
}

DT_LEN = {
    canopen.objectdictionary.BOOLEAN: 8,
    canopen.objectdictionary.INTEGER8: 8,
    canopen.objectdictionary.INTEGER16: 16,
    canopen.objectdictionary.INTEGER32: 32,
    canopen.objectdictionary.INTEGER64: 64,
    canopen.objectdictionary.UNSIGNED8: 8,
    canopen.objectdictionary.UNSIGNED16: 16,
    canopen.objectdictionary.UNSIGNED32: 32,
    canopen.objectdictionary.UNSIGNED64: 64,
    canopen.objectdictionary.VISIBLE_STRING: 0,
    canopen.objectdictionary.REAL32: 32,
    canopen.objectdictionary.REAL64: 64,
}


def make_obj_name(obj: canopen.objectdictionary.Variable) -> str:
    """get obj name."""

    name = ""
    if obj.index < 0x5000:
        name += "c3_"

    if isinstance(obj.parent, canopen.ObjectDictionary):
        name += obj.name
    else:
        name += f"{obj.parent.name}_{obj.name}"

    return name


def make_dt_name(obj: canopen.objectdictionary.Variable) -> str:
    """Make xtce data type name."""

    type_name = CANOPEN_TO_XTCE_DT[obj.data_type]
    if obj.name in ["unix_time", "updater_status"]:
        type_name = obj.name
    elif obj.value_descriptions:
        if isinstance(obj.parent, canopen.ObjectDictionary):
            type_name += f"_c3_{obj.name}"
        else:
            type_name += f"_{obj.parent.name}_{obj.name}"
    elif obj.data_type == canopen.objectdictionary.VISIBLE_STRING:
        type_name += f"{len(obj.default) * 8}"
    elif obj.unit:
        type_name += f"_{obj.unit}"
    type_name = type_name.replace("/", "p").replace("%", "percent")

    type_name += "_type"

    return type_name


def write_kaitai(config: OreSatConfig, dir_path: str = ".") -> None:
    """Write beacon configs to a kaitai file."""
    name = config.mission.name.lower().replace("_", ".")

    kaitai_data = {
        "meta": {
            "id": name,
            "title": f"{name} Decoder Struct",
            "endian": "le",
        },
        "doc": "",
        "seq": [
            {
                "id": "ax25_frame",
                "type": "ax25_frame",
                "doc-ref": "https://www.tapr.org/pub_ax25.html",
            }
        ],
        "types": {
            "ax25_frame": {
                "seq": [
                    {
                        "id": "ax25_header",
                        "type": "ax25_header",
                    },
                    {
                        "id": "payload",
                        "type": {
                            "switch-on": "ax25_header.ctl & 0x13",
                            "cases": {
                                "0x03": "ui_frame",
                                "0x13": "ui_frame",
                                "0x00": "i_frame",
                                "0x02": "i_frame",
                                "0x10": "i_frame",
                                "0x12": "i_framec",
                            },
                        },
                    },
                ]
            },
            "ax25_header": {
                "seq": [
                    {"id": "dest_callsign_raw", "type": "callsign_raw"},
                    {"id": "dest_ssid_raw", "type": "ssid_mask"},
                    {"id": "src_callsign_raw", "type": "callsign_raw"},
                    {"id": "src_ssid_raw", "type": "ssid_mask"},
                    {
                        "id": "repeater",
                        "type": "repeater",
                        "if": "(src_ssid_raw.ssid_mask & 0x01) == 0",
                        "doc": "Repeater flag is set!",
                    },
                    {"id": "ctl", "type": "u1"},
                ],
            },
            "repeater": {
                "seq": [
                    {
                        "id": "rpt_instance",
                        "type": "repeaters",
                        "repeat": "until",
                        "repeat-until": "until",
                        "doc": "Repeat until no repeater flag is set!",
                    }
                ]
            },
            "repeaters": {
                "seq": [
                    {
                        "id": "rpt_callsign_raw",
                        "type": "callsign_raw",
                    },
                    {
                        "id": "rpt_ssid_raw",
                        "type": "ssid_mask",
                    },
                ]
            },
            "callsign_raw": {
                "seq": [
                    {
                        "id": "callsign_ror",
                        "process": "repeaters",
                        "size": 6,
                        "type": "callsign",
                    }
                ]
            },
            "callsign": {
                "seq": [
                    {
                        "id": "callsign",
                        "type": "str",
                        "encoding": "ASCII",
                        "size": 6,
                        "valid": {"any-of": ['"KJ7SAT"', '"SPACE "']},
                    }
                ]
            },
            "ssid_mask": {
                "seq": [
                    {
                        "id": "ssid_mask",
                        "type": "u1",
                    }
                ],
                "instances": {"ssid": {"value": "(ssid_mask & 0x0f) >> 1"}},
            },
            "i_frame": {
                "seq": [
                    {
                        "id": "pid",
                        "type": "u1",
                    },
                    {"id": "ax25_info", "type": "ax25_info_data", "size-eos": True},
                ]
            },
            "ui_frame": {
                "seq": [
                    {
                        "id": "pid",
                        "type": "u1",
                    },
                    {"id": "ax25_info", "type": "ax25_info_data", "size-eos": True},
                ]
            },
            "ax25_info_data": {"seq": []},
        },
    }

    # Hard-code the 128b type for the AX.25 parameter
    for obj in config.beacon_def:
        new_var = {
            "id": obj.name,
            "type": CANOPEN_TO_KAITAI_DT[obj.data_type],
            "doc": obj.description,
        }
        if new_var["type"] == "str":
            new_var["encoding"] = "ASCII"
            if obj.access_type == "const":
                new_var["size"] = len(obj.default)
        kaitai_data["types"]["ax25_info_data"]["seq"].append(new_var)

    # write
    with open(f"{name}.ksy", "w+") as file:
        dump(kaitai_data, file)


def gen_kaitai(args: Optional[Namespace] = None) -> None:
    """Gen_dcf main."""
    if args is None:
        args = build_parser(ArgumentParser()).parse_args()

    config = OreSatConfig(args.oresat)
    write_kaitai(config, args.dir_path)
