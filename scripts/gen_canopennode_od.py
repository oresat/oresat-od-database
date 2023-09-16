#!/usr/bin/env python3
"""Generate a OreSat card's CANopenNode OD.[c/h] files"""

import math as m
import os
import sys
from argparse import ArgumentParser

_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{_FILE_PATH}/..")

import canopen

from oresat_od_db import oresat0, oresat0_5
from oresat_od_db._json_to_od import (
    RPDO_COMM_START,
    RPDO_PARA_START,
    TPDO_COMM_START,
    TPDO_PARA_START,
)

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


def format_name(string: str) -> str:
    """Convert object name to standard format"""

    if len(string) == 0:
        return ""  # nothing to do

    # remove invalid chars for variable names in C
    string = string.replace("-", "_").replace("(", " ").replace(")", " ")
    string = string.replace("  ", " ")

    s_list = string.split()

    name = ""
    for i in s_list:
        try:
            int(i)
        except ValueError:
            name += f"_{i}_"  # add '_' arounds numbers

    name = name.replace("__", "_")

    # remove any trailing '_'
    if name[-1] == "_":
        name = name[:-1]

    # remove any leading '_'
    if name[0] == "_":
        name = name[1:]

    name = name.lower()

    return name


def write_canopennode(od: canopen.ObjectDictionary, dir_path: str = "."):
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


def remove_node_id(default: str) -> str:
    """Remove "+$NODEID" or "$NODEID+" from the default value"""

    if not isinstance(default, str):
        return default

    temp = default.split("+")

    if default == "":
        return "0"
    if len(temp) == 1:
        return default  # does not include $NODEID
    if temp[0] == "$NODEID":
        return temp[1].rsplit()[0]
    if temp[1] == "$NODEID":
        return temp[0].rsplit()[0]

    return default  # does not include $NODEID


def attr_lines(od: canopen.ObjectDictionary, index: int) -> list:
    """Generate attr lines for OD.c for a sepecific index"""

    lines = []

    obj = od[index]
    if isinstance(obj, canopen.objectdictionary.Variable):
        default = remove_node_id(obj.default)
        line = f"{INDENT4}.x{index:X}_{format_name(obj.name)} = "

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
            line += f"0x{default:X},"
        else:
            line += f"{default},"

        if index not in _SKIP_INDEXES:
            lines.append(line)
    elif isinstance(obj, canopen.objectdictionary.Array):
        name = format_name(obj.name)
        lines.append(f"{INDENT4}.x{index:X}_{name}_sub0 = {obj[0].default},")
        line = f"{INDENT4}.x{index:X}_{name} = " + "{"

        if obj.data_type == canopen.objectdictionary.datatypes.DOMAIN:
            return lines  # skip domains

        for i in obj[1:]:
            default = remove_node_id(obj[i].default)

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
                line += f"0x{default:X}, "
            else:
                line += f"{default}, "

        line = line[:-2]  # remove trailing ', '
        line += "},"

        if index not in _SKIP_INDEXES:
            lines.append(line)
    else:  # ObjectType.Record
        lines.append(f"{INDENT4}.x{index:X}_{format_name(obj.name)} = " + "{")

        for i in obj:
            name = format_name(obj[i].name)
            if isinstance(obj[i].default, str):
                default = remove_node_id(obj[i].default)
            else:
                default = obj[i].default

            if obj[i].data_type == canopen.objectdictionary.datatypes.DOMAIN:
                continue  # skip domains

            if obj[i].name == "cob_id":
                # oresat firmware only wants 0x180, 0x280, 0x380, 0x480
                # no +node_id or +1, +2, +3 for TPDO nums > 4
                if default & 0xFFC not in [0x180, 0x280, 0x380, 0x480, 0x200, 0x300, 0x400, 0x500]:
                    cob_id = (default - od.node_id) & 0xFFC
                    cob_id += default & 0xC0_00_00_00  # add back pdo flags (2 MSBs)
                else:
                    cob_id = default
                lines.append(f"{INDENT8}.{name} = 0x{cob_id:X},")
            elif obj[i].data_type == canopen.objectdictionary.datatypes.VISIBLE_STRING:
                line = f"{INDENT8}.{name} = " + "{"
                for i in obj[i].default:
                    line += f"'{i}', "
                line += "0}, "
                lines.append(line)
            elif obj[i].data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
                value = obj[i].default.replace("  ", " ")
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
                lines.append(f"{INDENT8}.{name} = 0x{default:X},")
            else:
                lines.append(f"{INDENT8}.{name} = {default},")

        lines.append(INDENT4 + "},")

    return lines


def _var_data_type_len(var: canopen.objectdictionary.Variable) -> int:
    """Get the length of the variable's data in bytes"""

    if var.data_type == canopen.objectdictionary.datatypes.VISIBLE_STRING:
        length = len(var.default)  # char
    elif var.data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
        length = len(var.default.replace(" ", "")) // 2
    elif var.data_type == canopen.objectdictionary.datatypes.UNICODE_STRING:
        length = len(var.default) * 2  # uint16_t
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

    if var.data_type in DATA_TYPE_STR:
        attr_str += " | ODA_STR"
    elif (DATA_TYPE_C_SIZE[var.data_type] // 8) > 1:
        attr_str += " | ODA_MB"

    return attr_str


def obj_lines(od: canopen.ObjectDictionary, index) -> list:
    """Generate  lines for OD.c for a sepecific index"""

    lines = []

    obj = od[index]
    name = format_name(obj.name)
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

        if index in _SKIP_INDEXES or obj.data_type == canopen.objectdictionary.datatypes.DOMAIN:
            lines.append(f"{INDENT8}.dataOrig = NULL,")
        elif obj.data_type in [
            canopen.objectdictionary.datatypes.VISIBLE_STRING,
            canopen.objectdictionary.datatypes.OCTET_STRING,
            canopen.objectdictionary.datatypes.UNICODE_STRING,
        ]:
            lines.append(f"{INDENT8}.dataOrig = &OD_RAM.x{index:X}_{name}[0][0],")
        else:
            lines.append(f"{INDENT8}.dataOrig = &OD_RAM.x{index:X}_{name}[0],")

        lines.append(f"{INDENT8}.attribute0 = ODA_SDO_R,")
        lines.append(f"{INDENT8}.attribute = {_var_attr_flags(obj[1])},")
        length = _var_data_type_len(obj[1])
        lines.append(f"{INDENT8}.dataElementLength = {length},")

        c_name = DATA_TYPE_C_TYPES[obj.data_type]
        if obj.data_type == canopen.objectdictionary.datatypes.DOMAIN:
            lines.append(f"{INDENT8}.dataElementSizeof = 0,")
        elif obj.data_type in DATA_TYPE_STR:
            sub_length = len(obj[1].default) + 1  # add 1 for '\0'
            lines.append(f"{INDENT8}.dataElementSizeof = sizeof({c_name}[{sub_length}]),")
        elif obj.data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
            sub_length = m.ceil(len(obj[1].default.replace(" ", "")) / 2)
            lines.append(f"{INDENT8}.dataElementSizeof = sizeof({c_name}[{sub_length}]),")
        else:
            lines.append(f"{INDENT8}.dataElementSizeof = sizeof({c_name}),")
    else:  # ObjectType.DOMAIN
        for i in obj:
            name_sub = format_name(obj[i].name)
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


def write_canopennode_c(od: canopen.ObjectDictionary, dir_path: str = "."):
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
        name = format_name(od[i].name)
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
        name = format_name(od[i].name)
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


def _canopennode_h_lines(od: canopen.ObjectDictionary, index: int) -> list:
    """Generate struct lines for OD.h for a sepecific index"""

    lines = []

    obj = od[index]
    name = format_name(obj.name)

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
        c_name = DATA_TYPE_C_TYPES[obj.data_type]
        length_str = f"OD_CNT_ARR_{index:X}"
        lines.append(f"{INDENT4}uint8_t x{index:X}_{name}_sub0;")

        if obj.data_type == canopen.objectdictionary.datatypes.DOMAIN:
            pass  # skip domains
        elif index in _SKIP_INDEXES:
            pass
        elif obj.data_type in DATA_TYPE_STR:
            sub_length = len(obj[1].default) + 1  # add 1 for '\0'
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name}[{length_str}][{sub_length}];")
        elif obj.data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
            sub_length = m.ceil(len(obj[1].default.replace(" ", "")) / 2)
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name}[{length_str}][{sub_length}];")
        else:
            lines.append(f"{INDENT4}{c_name} x{index:X}_{name}[{length_str}];")
    else:
        lines.append(INDENT4 + "struct {")
        for i in obj:
            data_type = obj[i].data_type
            c_name = DATA_TYPE_C_TYPES[data_type]
            sub_name = format_name(obj[i].name)

            if data_type == canopen.objectdictionary.datatypes.DOMAIN:
                continue  # skip domains

            if data_type in DATA_TYPE_STR:
                length = len(obj[i].default) + 1  # add 1 for '\0'
                lines.append(f"{INDENT8}{c_name} {sub_name}[{length}];")
            elif data_type == canopen.objectdictionary.datatypes.OCTET_STRING:
                sub_length = m.ceil(len(obj[1].default.replace(" ", "")) / 2)
                lines.append(f"{INDENT8}{c_name} {sub_name}[{sub_length}];")
            else:
                lines.append(f"{INDENT8}{c_name} {sub_name};")

        lines.append(INDENT4 + "}" + f" x{index:X}_{name};")

    return lines


def write_canopennode_h(od: canopen.ObjectDictionary, dir_path: str = "."):
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

    lines.append("#define OD_CNT_NMT 1")
    lines.append("#define OD_CNT_EM 1")
    lines.append("#define OD_CNT_SYNC 1")
    lines.append("#define OD_CNT_SYNC_PROD 1")
    lines.append("#define OD_CNT_STORAGE 1")
    lines.append("#define OD_CNT_EM_PROD 1")
    lines.append("#define OD_CNT_HB_CONS 1")
    lines.append("#define OD_CNT_HB_PROD 1")
    lines.append("#define OD_CNT_SDO_SRV 1")
    if 0x1280 in od:
        lines.append("#define OD_CNT_SDO_CLI 1")
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

    for i in od:
        lines.append(f"#define OD_ENTRY_H{i:X} &OD->list[0x{i:X}]")
    lines.append("")

    for i in od:
        name = format_name(od[i].name)
        lines.append(f"#define OD_ENTRY_H{i:X}_{name.upper()} &OD->list[0x{i:X}]")
    lines.append("")

    # add nice #defines for indexes and subindex values
    for i in od:
        if i < 0x3000:
            continue  # only card about common, card, and RPDO mapped objects

        name = format_name(od[i].name)
        lines.append(f"#define OD_INDEX_{name.upper()} 0x{i:X}")

        for j in od[i]:
            if j == 0:
                continue
            sub_name = format_name(od[i][j].name)
            if i > 0x7000:  # RPDO mapped objects
                sub_name = f"{name}_{sub_name}"
            lines.append(f"#define OD_SUBINDEX_{sub_name.upper()} 0x{j:X}")
        lines.append("")

    lines.append("#endif /* OD_H */")

    with open(file_path, "w") as f:
        for i in lines:
            f.write(i + "\n")


OD_LIST = {
    ("oresat0", "c3"): oresat0.C3_OD,
    ("oresat0", "battery"): oresat0.BATTERY_1_OD,
    ("oresat0", "solar"): oresat0.SOLAR_MODULE_1_OD,
    ("oresat0", "imu"): oresat0.IMU_OD,
    ("oresat0.5", "battery"): oresat0_5.BATTERY_1_OD,
    ("oresat0.5", "solar"): oresat0_5.SOLAR_MODULE_1_OD,
    ("oresat0.5", "imu"): oresat0_5.IMU_OD,
    ("oresat0.5", "reaction_wheel"): oresat0_5.REACTION_WHEEL_1_OD,
}


def main():
    """The main"""

    parser = ArgumentParser("generate CANopenNode OD.[c/h] files")
    parser.add_argument("oresat", help="oresat mission; oresat0 or oresat0.5")
    parser.add_argument("card", help="card name; c3, battery, solar, imu, or reaction_wheel")
    parser.add_argument(
        "-d", "--dir-path", default=".", help='output directory path, default: "."'
    )
    args = parser.parse_args()

    if (args.oresat.lower(), args.card) not in OD_LIST:
        print("invalid oresat and/or card")
        sys.exit()

    od = OD_LIST[(args.oresat.lower(), args.card)]

    # need to add empty pdo indexes and subindexes
    for i in range(16):
        num = i + 1

        index = i + RPDO_COMM_START
        if index not in od:
            rec = canopen.objectdictionary.Record(f"rpdo_{num}_communication_parameters", index)
            od.add_object(rec)

            # index 0 for mapping index
            var = canopen.objectdictionary.Variable("highest_index_supported", index, 0x0)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 5
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("cob_id", index, 0x1)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED32
            var.default = ((i % 4) * 0x100) + 0x80000200  # disabled
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("transmission_type", index, 0x2)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 254  # event driven (delay-based or app specific)
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("event_timer", index, 0x5)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED16
            var.default = 0
            rec.add_member(var)

        index = i + RPDO_PARA_START
        if index not in od:
            rec = canopen.objectdictionary.Record(f"rpdo_{num}_mapping_parameters", index)
            od.add_object(rec)

            # index 0 for mapping index
            var = canopen.objectdictionary.Variable("highest_index_supported", index, 0x0)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 8
            rec.add_member(var)

            for subindex in range(1, 9):
                var = canopen.objectdictionary.Variable(
                    f"mapping_object_{subindex}", index, subindex
                )
                var.access_type = "const"
                var.data_type = canopen.objectdictionary.UNSIGNED32
                var.default = 0
                rec.add_member(var)
        else:
            for subindex in range(8):
                if subindex in od[index]:
                    continue

                var = canopen.objectdictionary.Variable(
                    f"mapping_object_{subindex}", index, subindex
                )
                var.access_type = "const"
                var.data_type = canopen.objectdictionary.UNSIGNED32
                var.default = 0
                od[index].add_member(var)
            od[index][0].default = 8

        index = i + TPDO_COMM_START
        if index not in od:
            rec = canopen.objectdictionary.Record(f"tpdo_{num}_communication_parameters", index)
            od.add_object(rec)

            # index 0 for mapping index
            var = canopen.objectdictionary.Variable("highest_index_supported", index, 0x0)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 6
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("cob_id", index, 0x1)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED32
            var.default = ((i % 4) * 0x100) + 0x80000180  # disabled
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("transmission_type", index, 0x2)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 254  # event driven (delay-based or app specific)
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("inhibit_time", index, 0x3)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED16
            var.default = 0
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("compatibility_entry", index, 0x4)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 0
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("event_timer", index, 0x5)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED16
            var.default = 0
            rec.add_member(var)

            var = canopen.objectdictionary.Variable("sync_start_value", index, 0x6)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 0
            rec.add_member(var)

        index = i + TPDO_PARA_START
        if index not in od:
            rec = canopen.objectdictionary.Record(f"tpdo_{num}_mapping_parameters", index)
            od.add_object(rec)

            # index 0 for mapping index
            var = canopen.objectdictionary.Variable("highest_index_supported", index, 0x0)
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 8
            rec.add_member(var)

            for subindex in range(1, 9):
                var = canopen.objectdictionary.Variable(
                    f"mapping_object_{subindex}", index, subindex
                )
                var.access_type = "const"
                var.data_type = canopen.objectdictionary.UNSIGNED32
                var.default = 0
                rec.add_member(var)
        else:
            for subindex in range(8):
                if subindex in od[index]:
                    continue

                var = canopen.objectdictionary.Variable(
                    f"mapping_object_{subindex}", index, subindex
                )
                var.access_type = "const"
                var.data_type = canopen.objectdictionary.UNSIGNED32
                var.default = 0
                od[index].add_member(var)
            od[index][0].default = 8

        od.device_information.nr_of_RXPDO = 16
        od.device_information.nr_of_TXPDO = 16

    write_canopennode(od, args.dir_path)


if __name__ == "__main__":
    main()
