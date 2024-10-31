"""Generate a OreSat card's CANopenNode OD.[c/h] files"""

import math as m
import os
import sys
from argparse import ArgumentParser, Namespace
from typing import Any, Optional

import canopen

from .. import Consts, OreSatConfig

GEN_FW_FILES = "generate CANopenNode OD.[c/h] files for a OreSat firmware card"


def build_parser(parser: ArgumentParser) -> ArgumentParser:
    """Configures an ArgumentParser suitable for this script.

    The given parser may be standalone or it may be used as a subcommand in another ArgumentParser.
    """
    parser.description = GEN_FW_FILES
    parser.add_argument(
        "--oresat",
        default=Consts.default().arg,
        choices=[m.arg for m in Consts],
        type=lambda x: x.lower().removeprefix("oresat"),
        help="Oresat Mission. (Default: %(default)s)",
    )
    parser.add_argument(
        "card", help="card name; c3, battery, solar, adcs, reaction_wheel, or diode_test"
    )
    parser.add_argument("-d", "--dir-path", default=".", help='output directory path, default: "."')
    parser.add_argument(
        "-hw", "--hardware-version", help="hardware board version string, usually defined in make"
    )
    parser.add_argument(
        "-fw", "--firmware-version", help="firmware version string, usually git describe output"
    )
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
    parser = build_parser(subparsers.add_parser("fw-files", help=GEN_FW_FILES))
    parser.set_defaults(func=gen_fw_files)


INDENT4 = " " * 4
INDENT8 = " " * 8
INDENT12 = " " * 12

_SKIP_INDEXES = [0x1F81, 0x1F82, 0x1F89]
"""CANopenNode skips the data (it just set to NULL) for these indexes for some reason"""

DATA_TYPE_STR = [
    canopen.objectdictionary.datatypes.VISIBLE_STRING,
    canopen.objectdictionary.datatypes.UNICODE_STRING,
]

DATA_TYPE_C_TYPES = {
    canopen.objectdictionary.datatypes.BOOLEAN: "bool_t",
    canopen.objectdictionary.datatypes.INTEGER8: "int8_t",
    canopen.objectdictionary.datatypes.INTEGER16: "int16_t",
    canopen.objectdictionary.datatypes.INTEGER32: "int32_t",
    canopen.objectdictionary.datatypes.UNSIGNED8: "uint8_t",
    canopen.objectdictionary.datatypes.UNSIGNED16: "uint16_t",
    canopen.objectdictionary.datatypes.UNSIGNED32: "uint32_t",
    canopen.objectdictionary.datatypes.REAL32: "float",
    canopen.objectdictionary.datatypes.VISIBLE_STRING: "char",
    canopen.objectdictionary.datatypes.OCTET_STRING: "uint8_t",
    canopen.objectdictionary.datatypes.UNICODE_STRING: "uint16_t",
    canopen.objectdictionary.datatypes.DOMAIN: None,
    canopen.objectdictionary.datatypes.REAL64: "double",
    canopen.objectdictionary.datatypes.INTEGER64: "int64_t",
    canopen.objectdictionary.datatypes.UNSIGNED64: "uint64_t",
}

DATA_TYPE_C_SIZE = {
    canopen.objectdictionary.datatypes.BOOLEAN: 8,
    canopen.objectdictionary.datatypes.INTEGER8: 8,
    canopen.objectdictionary.datatypes.INTEGER16: 16,
    canopen.objectdictionary.datatypes.INTEGER32: 32,
    canopen.objectdictionary.datatypes.UNSIGNED8: 8,
    canopen.objectdictionary.datatypes.UNSIGNED16: 16,
    canopen.objectdictionary.datatypes.UNSIGNED32: 32,
    canopen.objectdictionary.datatypes.REAL32: 32,
    canopen.objectdictionary.datatypes.REAL64: 64,
    canopen.objectdictionary.datatypes.INTEGER64: 64,
    canopen.objectdictionary.datatypes.UNSIGNED64: 64,
}


def write_canopennode(od: canopen.ObjectDictionary, dir_path: str = ".") -> None:
    """Save an od/dcf as CANopenNode OD.[c/h] files

    Parameters
    ----------
    od: canopen.ObjectDictionary
        OD data structure to save as file
    dir_path: str
        Path to directory to output OD.[c/h] to. If not set the same dir path as the od will
        be used.
    """

    if dir_path[-1] == "/":
        dir_path = dir_path[:-1]

    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)

    write_canopennode_c(od, dir_path)
    write_canopennode_h(od, dir_path)


def attr_lines(od: canopen.ObjectDictionary, index: int) -> list[str]:
    """Generate attr lines for OD.c for a sepecific index"""

    lines = []

    obj = od[index]
    if isinstance(obj, canopen.objectdictionary.Variable):
        line = f"{INDENT4}.x{index:X}_{obj.name} = "

        if obj.data_type == canopen.objectdictionary.datatypes.VISIBLE_STRING:
            line += "{"
            for i in obj.default:
                line += f'"{i}", '
            line += "0}, "
        elif obj.data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
            line += "{"
            value = obj.default.replace("  ", " ")
            for i in value.split(" "):
                line += f"0x{i}, "
            line = line[:-2]  # remove last ', '
            line += "},"
        elif obj.data_type == canopen.objectdictionary.datatypes.UNICODE_STRING:
            line += "{"
            for i in obj.default:
                line += f"0x{ord(i):04X}, "
            line += f"0x{0:04X}"  # add the '\0'
            line += "},"
        elif obj.data_type in canopen.objectdictionary.datatypes.INTEGER_TYPES:
            line += f"0x{obj.default:X},"
        elif obj.data_type == canopen.objectdictionary.datatypes.BOOLEAN:
            line += f"{int(obj.default)},"
        else:
            line += f"{obj.default},"

        if index not in _SKIP_INDEXES:
            lines.append(line)
    elif isinstance(obj, canopen.objectdictionary.Array):
        name = obj.name
        lines.append(f"{INDENT4}.x{index:X}_{name}_sub0 = {obj[0].default},")
        line = f"{INDENT4}.x{index:X}_{name} = " + "{"

        if obj[list(obj.subindices)[1]].data_type == canopen.objectdictionary.datatypes.DOMAIN:
            return lines  # skip domains

        for i in list(obj.subindices)[1:]:
            if obj[i].data_type == canopen.objectdictionary.datatypes.VISIBLE_STRING:
                line += "{"
                for i in obj[i].default:
                    line += f'"{i}", '
                line += "0}, "
            elif obj[i].data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
                line += "{"
                value = obj[i].default.replace("  ", " ")
                for i in value.split(" "):
                    line += f"0x{i}, "
                line = line[:-2]  # remove trailing ', '
                line += "}, "
            elif obj[i].data_type == canopen.objectdictionary.datatypes.UNICODE_STRING:
                line += "{"
                for i in obj[i].default:
                    line += f"0x{ord(i):04X}, "
                line += f"0x{0:04X}"  # add the '\0'
                line += "}, "
            elif obj[i].data_type in canopen.objectdictionary.datatypes.INTEGER_TYPES:
                line += f"0x{obj[i].default:X}, "
            elif obj[i].data_type == canopen.objectdictionary.datatypes.BOOLEAN:
                line += f"{int(obj[i].default)}, "
            else:
                line += f"{obj[i].default}, "

        line = line[:-2]  # remove trailing ', '
        line += "},"

        if index not in _SKIP_INDEXES:
            lines.append(line)
    else:  # ObjectType.Record
        lines.append(f"{INDENT4}.x{index:X}_{obj.name} = " + "{")

        for i in obj:
            name = obj[i].name
            if obj[i].data_type == canopen.objectdictionary.datatypes.DOMAIN:
                continue  # skip domains

            if obj[i].data_type == canopen.objectdictionary.datatypes.VISIBLE_STRING:
                line = f"{INDENT8}.{name} = " + "{"
                for i in obj[i].default:
                    line += f"'{i}', "
                line += "0}, "
                lines.append(line)
            elif obj[i].data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
                value = obj[i].default.hex(sep=" ")
                line = f"{INDENT8}.{name} = " + "{"
                for i in value.split(" "):
                    line += f"0x{i}, "
                line = line[:-2]  # remove trailing ', '
                line += "},"
                lines.append(line)
            elif obj[i].data_type == canopen.objectdictionary.datatypes.UNICODE_STRING:
                line = f"{INDENT8}.{name} = " + "{"
                for i in obj[i].default:
                    line += f"0x{ord(i):04X}, "
                line += f"0x{0:04X}"  # add the '\0'
                line += "},"
                lines.append(line)
            elif obj[i].data_type in canopen.objectdictionary.datatypes.INTEGER_TYPES:
                lines.append(f"{INDENT8}.{name} = 0x{obj[i].default:X},")
            elif obj[i].data_type == canopen.objectdictionary.datatypes.BOOLEAN:
                lines.append(f"{INDENT8}.{name} = {int(obj[i].default)},")
            else:
                lines.append(f"{INDENT8}.{name} = {obj[i].default},")

        lines.append(INDENT4 + "},")

    return lines


def _var_data_type_len(var: canopen.objectdictionary.Variable) -> int:
    """Get the length of the variable's data in bytes"""

    if var.data_type in [
        canopen.objectdictionary.datatypes.VISIBLE_STRING,
        canopen.objectdictionary.datatypes.OCTET_STRING,
    ]:
        length = len(var.default)  # char
    elif var.data_type == canopen.objectdictionary.datatypes.UNICODE_STRING:
        length = len(var.default) * 2  # uint16_t
    elif var.data_type == canopen.objectdictionary.datatypes.DOMAIN:
        length = 0
    else:
        length = DATA_TYPE_C_SIZE[var.data_type] // 8

    return length


def _var_attr_flags(var: canopen.objectdictionary.Variable) -> str:
    """Generate the variable attribute flags str"""

    attr_str = ""

    if var.access_type in ["ro", "const"]:
        attr_str += "ODA_SDO_R"
        if var.pdo_mappable:
            attr_str += " | ODA_TPDO"
    elif var.access_type == "wo":
        attr_str += "ODA_SDO_W"
        if var.pdo_mappable:
            attr_str += " | ODA_RPDO"
    else:
        attr_str += "ODA_SDO_RW"
        if var.pdo_mappable:
            attr_str += " | ODA_TRPDO"

    bytes_types = [
        canopen.objectdictionary.DOMAIN,
        canopen.objectdictionary.OCTET_STRING,
    ]
    if var.data_type in DATA_TYPE_STR:
        attr_str += " | ODA_STR"
    elif var.data_type in bytes_types or (DATA_TYPE_C_SIZE[var.data_type] // 8) > 1:
        attr_str += " | ODA_MB"

    return attr_str


def obj_lines(od: canopen.ObjectDictionary, index: int) -> list[str]:
    """Generate  lines for OD.c for a sepecific index"""

    lines = []

    obj = od[index]
    name = obj.name
    lines.append(f"{INDENT4}.o_{index:X}_{name} = " + "{")

    if isinstance(obj, canopen.objectdictionary.Variable):
        if index in _SKIP_INDEXES or obj.data_type == canopen.objectdictionary.datatypes.DOMAIN:
            lines.append(f"{INDENT8}.dataOrig = NULL,")
        elif (
            obj.data_type in DATA_TYPE_STR
            or obj.data_type == canopen.objectdictionary.datatypes.OCTET_STRING
        ):
            lines.append(f"{INDENT8}.dataOrig = &OD_RAM.x{index:X}_{name}[0],")
        else:
            lines.append(f"{INDENT8}.dataOrig = &OD_RAM.x{index:X}_{name},")

        lines.append(f"{INDENT8}.attribute = {_var_attr_flags(obj)},")
        lines.append(f"{INDENT8}.dataLength = {_var_data_type_len(obj)}")
    elif isinstance(obj, canopen.objectdictionary.Array):
        lines.append(f"{INDENT8}.dataOrig0 = &OD_RAM.x{index:X}_{name}_sub0,")

        first_obj = obj[list(obj.subindices)[1]]
        if (
            index in _SKIP_INDEXES
            or first_obj.data_type == canopen.objectdictionary.datatypes.DOMAIN
        ):
            lines.append(f"{INDENT8}.dataOrig = NULL,")
        elif first_obj.data_type in [
            canopen.objectdictionary.datatypes.VISIBLE_STRING,
            canopen.objectdictionary.datatypes.OCTET_STRING,
            canopen.objectdictionary.datatypes.UNICODE_STRING,
        ]:
            lines.append(f"{INDENT8}.dataOrig = &OD_RAM.x{index:X}_{name}[0][0],")
        else:
            lines.append(f"{INDENT8}.dataOrig = &OD_RAM.x{index:X}_{name}[0],")

        lines.append(f"{INDENT8}.attribute0 = ODA_SDO_R,")
        lines.append(f"{INDENT8}.attribute = {_var_attr_flags(first_obj)},")
        length = _var_data_type_len(first_obj)
        lines.append(f"{INDENT8}.dataElementLength = {length},")

        c_name = DATA_TYPE_C_TYPES[first_obj.data_type]
        if first_obj.data_type == canopen.objectdictionary.datatypes.DOMAIN:
            lines.append(f"{INDENT8}.dataElementSizeof = 0,")
        elif first_obj.data_type in DATA_TYPE_STR:
            sub_length = len(first_obj.default) + 1  # add 1 for '\0'
            lines.append(f"{INDENT8}.dataElementSizeof = sizeof({c_name}[{sub_length}]),")
        elif first_obj.data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
            sub_length = m.ceil(len(first_obj.default.replace(" ", "")) / 2)
            lines.append(f"{INDENT8}.dataElementSizeof = sizeof({c_name}[{sub_length}]),")
        else:
            lines.append(f"{INDENT8}.dataElementSizeof = sizeof({c_name}),")
    else:  # ObjectType.DOMAIN
        for i in obj:
            name_sub = obj[i].name
            lines.append(INDENT8 + "{")

            if obj[i].data_type == canopen.objectdictionary.datatypes.DOMAIN:
                lines.append(f"{INDENT12}.dataOrig = NULL,")
            elif obj[i].data_type in [
                canopen.objectdictionary.datatypes.VISIBLE_STRING,
                canopen.objectdictionary.datatypes.OCTET_STRING,
                canopen.objectdictionary.datatypes.UNICODE_STRING,
            ]:
                line = f"{INDENT12}.dataOrig = &OD_RAM.x{index:X}_{name}.{name_sub}[0],"
                lines.append(line)
            else:
                lines.append(f"{INDENT12}.dataOrig = &OD_RAM.x{index:X}_{name}.{name_sub},")

            lines.append(f"{INDENT12}.subIndex = {i},")
            lines.append(f"{INDENT12}.attribute = {_var_attr_flags(obj[i])},")
            lines.append(f"{INDENT12}.dataLength = {_var_data_type_len(obj[i])}")
            lines.append(INDENT8 + "},")

    lines.append(INDENT4 + "},")

    return lines


def write_canopennode_c(od: canopen.ObjectDictionary, dir_path: str = ".") -> None:
    """Save an od/dcf as a CANopenNode OD.c file

    Parameters
    ----------
    od: canopen.ObjectDictionary
        od data structure to save as file
    dir_path: str
        Path to directory to output OD.c to. If not set the same dir path as the od will
        be used.
    """

    lines = []

    if dir_path:
        file_path = dir_path + "/OD.c"
    else:  # use value od/dcf path
        file_path = "OD.c"

    lines.append("#define OD_DEFINITION")
    lines.append('#include "301/CO_ODinterface.h"')
    lines.append('#include "OD.h"')
    lines.append("")

    lines.append("#if CO_VERSION_MAJOR < 4")
    lines.append("#error This file is only comatible with CANopenNode v4 and above")
    lines.append("#endif")
    lines.append("")

    lines.append("OD_ATTR_RAM OD_RAM_t OD_RAM = {")
    for j in od:
        lines += attr_lines(od, j)
    lines.append("};")
    lines.append("")

    lines.append("typedef struct {")
    for i in od:
        name = od[i].name
        if isinstance(od[i], canopen.objectdictionary.Variable):
            lines.append(f"{INDENT4}OD_obj_var_t o_{i:X}_{name};")
        elif isinstance(od[i], canopen.objectdictionary.Array):
            lines.append(f"{INDENT4}OD_obj_array_t o_{i:X}_{name};")
        else:
            size = len(od[i])
            lines.append(f"{INDENT4}OD_obj_record_t o_{i:X}_{name}[{size}];")
    lines.append("} ODObjs_t;")
    lines.append("")

    lines.append("static CO_PROGMEM ODObjs_t ODObjs = {")
    for i in od:
        lines += obj_lines(od, i)
    lines.append("};")
    lines.append("")

    lines.append("static OD_ATTR_OD OD_entry_t ODList[] = {")
    for i in od:
        name = od[i].name
        if isinstance(od[i], canopen.objectdictionary.Variable):
            length = 1
            obj_type = "ODT_VAR"
        elif isinstance(od[i], canopen.objectdictionary.Array):
            length = len(od[i])
            obj_type = "ODT_ARR"
        else:
            length = len(od[i])
            obj_type = "ODT_REC"
        temp = f"0x{i:X}, 0x{length:02X}, {obj_type}, &ODObjs.o_{i:X}_{name}, NULL"
        lines.append(INDENT4 + "{" + temp + "},")
    lines.append(INDENT4 + "{0x0000, 0x00, 0, NULL, NULL}")
    lines.append("};")
    lines.append("")

    lines.append("static OD_t _OD = {")
    lines.append(f"{INDENT4}(sizeof(ODList) / sizeof(ODList[0])) - 1,")
    lines.append(f"{INDENT4}&ODList[0]")
    lines.append("};")
    lines.append("")

    lines.append("OD_t *OD = &_OD;")

    with open(file_path, "w") as f:
        for i in lines:
            f.write(i + "\n")


def _canopennode_h_lines(od: canopen.ObjectDictionary, index: int) -> list[str]:
    """Generate struct lines for OD.h for a sepecific index"""

    lines = []

    obj = od[index]
    name = obj.name

    if isinstance(obj, canopen.objectdictionary.Variable):
        c_name = DATA_TYPE_C_TYPES[obj.data_type]

        if obj.data_type == canopen.objectdictionary.datatypes.DOMAIN:
            pass  # skip domains
        elif obj.data_type in DATA_TYPE_STR:
            length = len(obj.default) + 1  # add 1 for '\0'
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name}[{length}];")
        elif obj.data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
            length = len(obj.default.replace(" ", "")) // 2  # aka number of uint8s
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name}[{length}];")
        else:
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name};")
    elif isinstance(obj, canopen.objectdictionary.Array):
        first_obj = obj[list(obj.subindices)[1]]
        c_name = DATA_TYPE_C_TYPES[first_obj.data_type]
        length_str = f"OD_CNT_ARR_{index:X}"
        lines.append(f"{INDENT4}uint8_t x{index:X}_{name}_sub0;")

        if first_obj.data_type == canopen.objectdictionary.datatypes.DOMAIN:
            pass  # skip domains
        elif index in _SKIP_INDEXES:
            pass
        elif first_obj.data_type in DATA_TYPE_STR:
            sub_length = len(first_obj.default) + 1  # add 1 for '\0'
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name}[{length_str}][{sub_length}];")
        elif first_obj.data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
            sub_length = m.ceil(len(first_obj.default.replace(" ", "")) / 2)
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name}[{length_str}][{sub_length}];")
        else:
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name}[{length_str}];")
    else:
        lines.append(INDENT4 + "struct {")
        for i in obj:
            data_type = obj[i].data_type
            c_name = DATA_TYPE_C_TYPES[data_type]
            sub_name = obj[i].name

            if data_type == canopen.objectdictionary.datatypes.DOMAIN:
                continue  # skip domains

            if data_type in DATA_TYPE_STR:
                length = len(obj[i].default) + 1  # add 1 for '\0'
                lines.append(f"{INDENT8}{c_name} {sub_name}[{length}];")
            elif data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
                sub_length = len(obj[list(obj.subindices)[1]].default)
                lines.append(f"{INDENT8}{c_name} {sub_name}[{sub_length}];")
            else:
                lines.append(f"{INDENT8}{c_name} {sub_name};")

        lines.append(INDENT4 + "}" + f" x{index:X}_{name};")

    return lines


def write_canopennode_h(od: canopen.ObjectDictionary, dir_path: str = ".") -> None:
    """Save an od/dcf as a CANopenNode OD.h file

    Parameters
    ----------
    od: canopen.ObjectDictionary
        od data structure to save as file
    dir_path: str
        Path to directory to output OD.h to. If not set the same dir path as the od will
        be used.
    """

    lines = []

    if dir_path:
        file_path = dir_path + "/OD.h"
    else:  # use value od/dcf path
        file_path = "OD.h"

    lines.append("#ifndef OD_H")
    lines.append("#define OD_H")
    lines.append("")
    lines.append("#include <assert.h>")
    lines.append("")

    lines.append("#define OD_CNT_NMT 1")
    lines.append("#define OD_CNT_HB_PROD 1")
    lines.append(f"#define OD_CNT_HB_CONS {int(0x1016 in od)}")
    lines.append("#define OD_CNT_EM 1")
    lines.append("#define OD_CNT_EM_PROD 1")
    lines.append(f"#define OD_CNT_SDO_SRV {int(0x1200 in od)}")
    lines.append(f"#define OD_CNT_SDO_CLI {int(0x1280 in od)}")
    lines.append(f"#define OD_CNT_TIME {int(0x1012 in od)}")
    lines.append(f"#define OD_CNT_SYNC {int(0x1005 in od and 0x1006 in od)}")
    lines.append(f"#define OD_CNT_RPDO {od.device_information.nr_of_RXPDO}")
    lines.append(f"#define OD_CNT_TPDO {od.device_information.nr_of_TXPDO}")
    lines.append("")

    for i in od:
        if isinstance(od[i], canopen.objectdictionary.Array):
            lines.append(f"#define OD_CNT_ARR_{i:X} {len(od[i]) - 1}")
    lines.append("")

    lines.append("typedef struct {")
    for j in od:
        lines += _canopennode_h_lines(od, j)
    lines.append("} OD_RAM_t;")
    lines.append("")

    lines.append("#ifndef OD_ATTR_RAM")
    lines.append("#define OD_ATTR_RAM")
    lines.append("#endif")
    lines.append("extern OD_ATTR_RAM OD_RAM_t OD_RAM;")
    lines.append("")

    lines.append("#ifndef OD_ATTR_OD")
    lines.append("#define OD_ATTR_OD")
    lines.append("#endif")
    lines.append("extern OD_ATTR_OD OD_t *OD;")
    lines.append("")

    num = 0
    for i in od:
        lines.append(f"#define OD_ENTRY_H{i:X} &OD->list[{num}]")
        num += 1
    lines.append("")

    num = 0
    for i in od:
        name = od[i].name
        lines.append(f"#define OD_ENTRY_H{i:X}_{name.upper()} &OD->list[{num}]")
        num += 1
    lines.append("")

    # add nice #defines for indexes and subindex values
    for i in od:
        if i < 0x2000:
            continue  # only care about common, card, and RPDO mapped objects

        name = od[i].name
        lines.append(f"#define OD_INDEX_{name.upper()} 0x{i:X}")

        if not isinstance(od[i], canopen.objectdictionary.Variable):
            for j in od[i]:
                if j == 0:
                    continue
                sub_name = f"{name}_" + od[i][j].name
                lines.append(f"#define OD_SUBINDEX_{sub_name.upper()} 0x{j:X}")
        lines.append("")

    for obj in od.values():
        if isinstance(obj, canopen.objectdictionary.Variable):
            lines += _make_enum_lines(obj)
        elif isinstance(obj, canopen.objectdictionary.Array):
            subindex = list(obj.subindices.keys())[1]
            lines += _make_enum_lines(obj[subindex])
        else:
            for subindex, sub_obj in obj.subindices.items():
                lines += _make_enum_lines(sub_obj)

    for obj in od.values():
        if isinstance(obj, canopen.objectdictionary.Variable):
            lines += _make_bitfields_lines(obj)
        elif isinstance(obj, canopen.objectdictionary.Array):
            subindex = list(obj.subindices.keys())[1]
            lines += _make_bitfields_lines(obj[subindex])
        else:
            for subindex in obj.subindices:
                lines += _make_bitfields_lines(obj[subindex])

    lines.append("#endif /* OD_H */")

    with open(file_path, "w") as f:
        for i in lines:
            f.write(i + "\n")


def _make_enum_lines(obj: canopen.objectdictionary.Variable) -> list[str]:
    lines: list[str] = []
    if not obj.value_descriptions:
        return lines

    obj_name = obj.name
    if isinstance(obj.parent, canopen.objectdictionary.Record):
        obj_name = f"{obj.parent.name}_{obj_name}"
    elif isinstance(obj.parent, canopen.objectdictionary.Array):
        obj_name = obj.parent.name

    lines.append(f"enum {obj_name}_enum " + "{")
    for value, name in obj.value_descriptions.items():
        lines.append(f"{INDENT4}{obj_name.upper()}_{name.upper()} = {value},")
    lines.append("};")
    lines.append("")

    return lines


def _make_bitfields_lines(obj: canopen.objectdictionary.Variable) -> list[str]:
    lines: list[str] = []
    if not obj.bit_definitions:
        return lines

    obj_name = obj.name
    if isinstance(obj.parent, canopen.objectdictionary.Record):
        obj_name = f"{obj.parent.name}_{obj_name}"
    elif isinstance(obj.parent, canopen.objectdictionary.Array):
        obj_name = obj.parent.name

    data_type = DATA_TYPE_C_TYPES[obj.data_type]
    bitfield_name = obj_name + "_bitfield"
    lines.append(f"union {bitfield_name} " + "{")
    lines.append(f"{INDENT4}{data_type} value;")
    lines.append(INDENT4 + "struct __attribute((packed)) {")
    total_bits = 0

    sorted_keys = sorted(obj.bit_definitions, key=lambda k: max(obj.bit_definitions.get(k)))
    bit_defs = {key: obj.bit_definitions[key] for key in sorted_keys}

    for name, bits in bit_defs.items():
        if total_bits < min(bits):
            unused_bits = min(bits) - total_bits
            lines.append(f"{INDENT8}{data_type} unused{total_bits} : {unused_bits};")
            total_bits += unused_bits
        lines.append(f"{INDENT8}{data_type} {name.lower()} : {len(bits)};")
        total_bits += len(bits)
    if total_bits < DATA_TYPE_C_SIZE[obj.data_type]:
        unused_bits = DATA_TYPE_C_SIZE[obj.data_type] - total_bits
        lines.append(f"{INDENT8}{data_type} unused{total_bits} : {unused_bits};")
    lines.append(INDENT4 + "} fields;")
    lines.append("};")
    lines.append(
        f"static_assert(sizeof({bitfield_name}) == sizeof({data_type}), "
        '"pack size did not match value size");'
    )
    lines.append("")

    return lines


def gen_fw_files(args: Optional[Namespace] = None) -> None:
    """generate CANopenNode firmware files main"""
    if args is None:
        args = build_parser(ArgumentParser()).parse_args()

    config = OreSatConfig(args.oresat)

    arg_card = args.card.lower().replace("-", "_")
    if arg_card == "c3":
        od = config.od_db["c3"]
    elif arg_card in ["solar", "solar_module"]:
        od = config.od_db["solar_1"]
    elif arg_card in ["battery", "bat"]:
        od = config.od_db["battery_1"]
    elif arg_card in ["imu", "adcs"]:
        od = config.od_db["adcs"]
    elif arg_card in ["rw", "reaction_wheel"]:
        od = config.od_db["rw_1"]
    elif arg_card in ["diode", "diode_test"]:
        od = config.od_db["diode_test"]
    elif arg_card == "base":
        od = config.fw_base_od
    else:
        print(f"invalid oresat card: {args.card}")
        sys.exit()

    if args.hardware_version is not None:
        od["versions"]["hw_version"].default = args.hardware_version
    if args.firmware_version is not None:
        od["versions"]["fw_version"].default = args.firmware_version

    # remove node id from emcy cob id
    if 0x1014 in od:
        od[0x1014].default = 0x80

    max_pdos = 12 if arg_card == "c3" else 16
    tpdo_cob_ids = [0x180 + (0x100 * (i % 4)) + (i // 4) + od.node_id for i in range(max_pdos)]
    rpdo_cob_ids = [i + 0x80 for i in tpdo_cob_ids]

    def _remove_pdo_cob_ids(start: int, num: int, cob_ids: list[int]):
        for index in range(start, start + num):
            obj = od[index]
            default = obj[1].default
            if default & 0x7FF in cob_ids:
                cob_id = (default - od.node_id) & 0xFFC
                cob_id += default & 0xC0_00_00_00  # add back pdo flags (2 MSBs)
            else:
                cob_id = default
            obj[1].default = cob_id

    # remove node id from pdo cob ids
    _remove_pdo_cob_ids(0x1400, od.device_information.nr_of_RXPDO, rpdo_cob_ids)
    _remove_pdo_cob_ids(0x1800, od.device_information.nr_of_TXPDO, tpdo_cob_ids)

    write_canopennode(od, args.dir_path)
