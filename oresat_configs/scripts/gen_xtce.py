"""
Generate XTCE for the beacon.

To validate generated XTCE
- download the xsd:
  curl -O https://www.omg.org/spec/XTCE/20180204/SpaceSystem.xsd
- run xmllint:
  xmllint --noout --schema SpaceSystem.xsd *.xtce
"""

import xml.etree.ElementTree as ET
from argparse import ArgumentParser, Namespace
from datetime import datetime
from typing import Any, Optional

import canopen

from .. import Consts, EdlCommandField, OreSatConfig, __version__

GEN_XTCE = "generate beacon xtce file"


def build_parser(parser: ArgumentParser) -> ArgumentParser:
    """Configures an ArgumentParser suitable for this script.

    The given parser may be standalone or it may be used as a subcommand in another ArgumentParser.
    """
    parser.description = GEN_XTCE
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
    parser = build_parser(subparsers.add_parser("xtce", help=GEN_XTCE))
    parser.set_defaults(func=gen_xtce)


CANOPEN_TO_XTCE_DT = {
    canopen.objectdictionary.BOOLEAN: "bool",
    canopen.objectdictionary.INTEGER8: "int8",
    canopen.objectdictionary.INTEGER16: "int16",
    canopen.objectdictionary.INTEGER32: "int32",
    canopen.objectdictionary.INTEGER64: "int64",
    canopen.objectdictionary.UNSIGNED8: "uint8",
    canopen.objectdictionary.UNSIGNED16: "uint16",
    canopen.objectdictionary.UNSIGNED32: "uint32",
    canopen.objectdictionary.UNSIGNED64: "uint64",
    canopen.objectdictionary.VISIBLE_STRING: "str",
    canopen.objectdictionary.OCTET_STRING: "bytes",
    canopen.objectdictionary.REAL32: "float32",
    canopen.objectdictionary.REAL64: "float64",
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
    canopen.objectdictionary.OCTET_STRING: 0,
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


def write_xtce(config: OreSatConfig, dir_path: str = ".") -> None:
    """Write beacon configs to a xtce file."""

    root = ET.Element(
        "SpaceSystem",
        attrib={
            "name": config.mission.filename(),
            "xmlns": "http://www.omg.org/spec/XTCE/20180204",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": (
                "http://www.omg.org/spec/XTCE/20180204 "
                "https://www.omg.org/spec/XTCE/20180204/SpaceSystem.xsd"
            ),
        },
    )

    header = ET.SubElement(
        root,
        "Header",
        attrib={
            "validationStatus": "Working",
            "classification": "NotClassified",
            "version": f"{__version__}",
            "date": datetime.now().strftime("%Y-%m-%d"),
        },
    )
    author_set = ET.SubElement(header, "AuthorSet")
    author = ET.SubElement(author_set, "Author")
    author.text = "PSAS (Portland State Aerospace Society)"

    tm_meta = ET.SubElement(root, "TelemetryMetaData")
    para_type_set = ET.SubElement(tm_meta, "ParameterTypeSet")

    para_set = ET.SubElement(tm_meta, "ParameterSet")

    cont_set = ET.SubElement(tm_meta, "ContainerSet")
    seq_cont = ET.SubElement(
        cont_set,
        "SequenceContainer",
        attrib={
            "name": "beacon",
        },
    )
    beacon_entry_list = ET.SubElement(seq_cont, "EntryList")
    ET.SubElement(
        beacon_entry_list,
        "ParameterRefEntry",
        attrib={"parameterRef": "ax25_header"},
    )

    # hard-code data type
    _add_parameter_type(para_type_set, "b128_type", "bytes", default=b"\x00" * 16)
    _add_parameter_type(para_type_set, "unix_time_type", "unix_time")
    _add_parameter_type(para_type_set, "uint32_type", "uint32")
    para_types = ["unix_time_type", "b128_type", "uint32_type"]

    # beacon headers
    _add_parameter(para_set, "ax25_header", "b128_type", "AX.25 Header")
    _add_parameter_ref(beacon_entry_list, "ax25_header")

    for obj in config.beacon_def:
        para_name = make_obj_name(obj)
        para_type_name = make_dt_name(obj)
        if para_type_name not in para_types:
            para_types.append(para_type_name)

            data_type = CANOPEN_TO_XTCE_DT[obj.data_type]
            value_descriptions = {name: value for value, name in obj.value_descriptions.items()}
            _add_parameter_type(
                root=para_type_set,
                name=para_type_name,
                data_type=data_type,
                description=obj.description,
                unit=obj.unit,
                factor=obj.factor,
                default=obj.default,
                value_descriptions=value_descriptions,
            )

        _add_parameter(para_set, para_name, para_type_name, obj.description)
        _add_parameter_ref(beacon_entry_list, para_name)

    # beacon tails
    _add_parameter(para_set, "crc32", "uint32_type", "beacon crc32")
    _add_parameter_ref(beacon_entry_list, "crc32")

    # OreSat0 was before oresat-configs and had different commands
    if config.mission != Consts.ORESAT0:
        _add_edl(config, root, cont_set, para_type_set, para_set, para_types)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    file_name = f"{config.mission.filename()}.xtce"
    tree.write(f"{dir_path}/{file_name}", encoding="utf-8", xml_declaration=True)


def _add_edl(
    config: OreSatConfig,
    root: ET.Element,
    cont_set: ET.Element,
    para_type_set: ET.Element,
    para_set: ET.Element,
    para_types: list[str],
):
    cmd_meta_data = ET.SubElement(root, "CommandMetaData")
    arg_type_set = ET.SubElement(cmd_meta_data, "ArgumentTypeSet")

    # custom argument types
    node_ids = {}
    for name in config.od_db:
        if config.cards[name].node_id != 0:
            node_ids[config.cards[name].nice_name] = config.cards[name].node_id
    _add_argument_type(
        arg_type_set, EdlCommandField("node_id", "uint8", enums=node_ids), "node_id_type"
    )
    opd_addrs = {}
    for name in config.od_db:
        if config.cards[name].opd_address != 0:
            opd_addrs[config.cards[name].nice_name] = config.cards[name].opd_address
    _add_argument_type(
        arg_type_set, EdlCommandField("opd_addr", "uint8", enums=opd_addrs), "opd_addr_type"
    )

    arg_types = ["opd_addr_type", "node_id_type"]

    _add_parameter_type(
        para_type_set,
        "edl_command_code_type",
        "uint8",
        value_descriptions={cmd.name: cmd.uid for cmd in config.edl_cmd_defs.values()},
    )
    _add_parameter(para_set, "edl_command_code", "edl_command_code_type")
    res_seq_cont = ET.SubElement(
        cont_set,
        "SequenceContainer",
        attrib={
            "name": "edl_responses",
        },
    )
    res_entry_list = ET.SubElement(res_seq_cont, "EntryList")
    ET.SubElement(
        res_entry_list,
        "ParameterRefEntry",
        attrib={"parameterRef": "edl_command_code"},
    )
    meta_cmd_set = ET.SubElement(cmd_meta_data, "MetaCommandSet")

    # uslp containers
    meta_cmd = ET.SubElement(
        meta_cmd_set, "MetaCommand", attrib={"name": "uslp_header", "abstract": "true"}
    )
    uslp_header_cont = ET.SubElement(meta_cmd, "CommandContainer", attrib={"name": "uslp_header"})
    uslp_header_entry_list = ET.SubElement(uslp_header_cont, "EntryList")

    # fill uslp transfer frame container
    uslp_fields = [
        # uslp primary header
        (EdlCommandField("version_number", "uint4"), 0xC),
        (EdlCommandField("spacecraft_id", "uint16"), 0x4F53),
        (EdlCommandField("src_dest", "bool"), 0),
        (EdlCommandField("virtual_channel_id", "uint6"), 0),
        (EdlCommandField("map_id", "uint4"), 0),
        (EdlCommandField("eof_flag", "bool"), 0),
        (EdlCommandField("frame_length", "uint16"), 0),
        (EdlCommandField("bypass_sequence_control_flag", "bool"), 0),
        (EdlCommandField("protocol_control_command_flag", "bool"), 0),
        (EdlCommandField("reserved", "uint2"), 0),
        (EdlCommandField("operation_control_field_flag", "bool"), 0),
        (EdlCommandField("vc_frame_count_length", "uint3"), 0),
        # uslp transfer frame insert zone
        (EdlCommandField("sequence_number", "uint32"), 0),
        # uslp data field header
        (EdlCommandField("tfdz_contruction_rules", "uint3"), 0x7),
        (EdlCommandField("protocol_id", "uint5"), 0x5),
    ]

    uslp_seq_cont = ET.SubElement(
        cont_set,
        "SequenceContainer",
        attrib={"name": "uslp_header", "abstract": "true"},
    )
    uslp_entry_list = ET.SubElement(uslp_seq_cont, "EntryList")

    _add_parameter_type(para_type_set, "bytes_hmac_type", "bytes", default="00" * 32)
    _add_parameter(para_set, "hmac", "bytes_hmac_type")
    _add_parameter(para_set, "uslp_fecf", "uint32_type")

    for subpacket, fixed_value in uslp_fields:
        size = "1" if subpacket.data_type == "bool" else subpacket.data_type[4:]
        if int(size) > 16 and int(size) <= 32:
            value = f"{fixed_value:08X}"
        elif int(size) > 8 and int(size) <= 16:
            value = f"{fixed_value:04X}"
        else:
            value = f"{fixed_value:02X}"

        para_name = f"uslp_{subpacket.name}"

        # add uslp subpacket to telemetery
        para_type_name = f"{subpacket.data_type}_type"
        if para_type_name not in para_types:
            para_types.append(para_type_name)
            _add_parameter_type(para_type_set, para_type_name, subpacket.data_type)
        _add_parameter(para_set, para_name, para_type_name)
        _add_parameter_ref(uslp_entry_list, para_name)

        # add uslp subpacket to telecommand
        ET.SubElement(
            uslp_header_entry_list,
            "FixedValueEntry",
            attrib={"name": para_name, "binaryValue": value, "sizeInBits": size},
        )
    uslp_entry_list.append(ET.Comment("child containers go here"))
    para_ref_entry = _add_parameter_ref(uslp_entry_list, "hmac")
    loc_in_cont = ET.SubElement(
        para_ref_entry, "LocationInContainerInBits", attrib={"referenceLocation": "nextEntry"}
    )
    fixed_value = ET.SubElement(loc_in_cont, "FixedValue")
    fixed_value.text = str(32 * 8 + 16)
    para_ref_entry = _add_parameter_ref(uslp_entry_list, "uslp_fecf")
    loc_in_cont = ET.SubElement(
        para_ref_entry, "LocationInContainerInBits", attrib={"referenceLocation": "containerEnd"}
    )
    fixed_value = ET.SubElement(loc_in_cont, "FixedValue")
    fixed_value.text = "16"

    for cmd in config.edl_cmd_defs.values():
        # add command
        meta_cmd = ET.SubElement(meta_cmd_set, "MetaCommand", attrib={"name": cmd.name})
        if cmd.description:
            meta_cmd.attrib["shortDescription"] = cmd.description
        if cmd.request:
            # this must be added before CommandContainer, if it exist
            arg_list = ET.SubElement(meta_cmd, "ArgumentList")
        cmd_cont = ET.SubElement(
            meta_cmd, "CommandContainer", attrib={"name": f"{cmd.name}_request"}
        )
        cmd_entry_list = ET.SubElement(cmd_cont, "EntryList")

        ET.SubElement(cmd_cont, "BaseContainer", attrib={"containerRef": "uslp_header"})

        ET.SubElement(
            cmd_entry_list,
            "FixedValueEntry",
            attrib={
                "binaryValue": f"{cmd.uid:02X}",
                "sizeInBits": "8",
            },
        )

        # add command argument(s)
        if cmd.request:
            for req_field in cmd.request:
                if req_field.size_prefix > 0:
                    data_type = f"uint{req_field.size_prefix * 8}"
                    type_name = f"{data_type}_type"
                    name = f"{req_field.name}_size"
                    if type_name not in arg_types:
                        arg_types.append(type_name)
                        _add_argument_type(
                            arg_type_set, EdlCommandField(name, data_type), type_name
                        )
                    ET.SubElement(
                        arg_list,
                        "Argument",
                        attrib={
                            "name": name,
                            "argumentTypeRef": type_name,
                        },
                    )
                    ET.SubElement(
                        cmd_entry_list,
                        "ArgumentRefEntry",
                        attrib={"argumentRef": name},
                    )

                if req_field.name in ["opd_addr", "node_id"]:
                    type_name = req_field.name + "_type"
                else:
                    type_name = req_field.data_type + "_type"

                if type_name not in arg_types:
                    arg_types.append(type_name)
                    _add_argument_type(arg_type_set, req_field, type_name)
                ET.SubElement(
                    arg_list,
                    "Argument",
                    attrib={
                        "name": req_field.name,
                        "argumentTypeRef": type_name,
                    },
                )
                ET.SubElement(
                    cmd_entry_list,
                    "ArgumentRefEntry",
                    attrib={"argumentRef": req_field.name},
                )

        ET.SubElement(
            cmd_entry_list,
            "FixedValueEntry",
            attrib={"name": "hmac", "binaryValue": "0" * 64, "sizeInBits": str(32 * 8)},
        )
        ET.SubElement(
            cmd_entry_list,
            "FixedValueEntry",
            attrib={"name": "uslp_fecf", "binaryValue": "0000", "sizeInBits": "16"},
        )

        # add command parameter(s)
        if cmd.response:
            container_name = f"{cmd.name}_response"
            seq_cont = ET.SubElement(
                cont_set,
                "SequenceContainer",
                attrib={"name": container_name},
            )
            entry_list = ET.SubElement(seq_cont, "EntryList")
            ET.SubElement(seq_cont, "BaseContainer", attrib={"containerRef": "uslp_header"})
            for res_field in cmd.response:
                para_name = f"{cmd.name}_{res_field.name}"
                para_ref = ""
                if res_field.size_prefix > 0:
                    # add buffer size parameter
                    para_data_type = f"uint{res_field.size_prefix * 8}"
                    para_type_name = f"{para_name}_type"
                    if para_type_name not in para_types:
                        para_types.append(para_type_name)
                        _add_parameter_type(
                            para_type_set,
                            para_type_name,
                            para_data_type,
                        )
                    para_ref = f"{para_name}_size"
                    _add_parameter(para_set, para_ref, para_type_name)
                    _add_parameter_ref(entry_list, para_ref)

                if res_field.unit:
                    para_type_name = f"{res_field.data_type}_{res_field.unit}_type"
                else:
                    para_type_name = f"{res_field.data_type}_type"

                if para_type_name not in para_types:
                    para_types.append(para_type_name)
                    _add_parameter_type(
                        para_type_set,
                        para_type_name,
                        res_field.data_type,
                        unit=res_field.unit,
                        value_descriptions=res_field.enums,
                        size_prefix=res_field.size_prefix,
                        param_ref=para_ref,
                    )

                _add_parameter(para_set, para_name, para_type_name, res_field.description)
                _add_parameter_ref(entry_list, para_name)

            cont_ref_entry = ET.SubElement(
                res_entry_list,
                "ContainerRefEntry",
                attrib={
                    "containerRef": container_name,
                },
            )
            inc_cond = ET.SubElement(cont_ref_entry, "IncludeCondition")
            ET.SubElement(
                inc_cond,
                "Comparison",
                attrib={
                    "parameterRef": "edl_command_code",
                    "value": str(cmd.uid),
                },
            )


def gen_xtce(args: Optional[Namespace] = None) -> None:
    """Gen_dcf main."""
    if args is None:
        args = build_parser(ArgumentParser()).parse_args()

    config = OreSatConfig(args.oresat)
    write_xtce(config, args.dir_path)


def _add_parameter_type(
    root,
    name: str,
    data_type: str,
    description: str = "",
    unit: str = "",
    factor: float = 1,
    default: Any = None,
    value_descriptions: dict[str, int] = {},
    size_prefix: int = 0,
    param_ref: str = "",
):

    if data_type == "bool":
        para_type = ET.SubElement(
            root,
            "BooleanParameterType",
            attrib={
                "name": name,
                "zeroStringValue": "0",
                "oneStringValue": "1",
            },
        )
        ET.SubElement(
            para_type,
            "IntegerDataEncoding",
            attrib={
                "byteOrder": "leastSignificantByteFirst",
                "encoding": "unsigned",
                "sizeInBits": "8",
            },
        )
    elif data_type.startswith("uint") and value_descriptions:  # enums
        para_type = ET.SubElement(
            root,
            "EnumeratedParameterType",
            attrib={
                "name": name,
            },
        )
        ET.SubElement(
            para_type,
            "IntegerDataEncoding",
            attrib={
                "byteOrder": "leastSignificantByteFirst",
                "encoding": "unsigned",
                "sizeInBits": data_type[4:],
            },
        )
        enum_list = ET.SubElement(para_type, "EnumerationList")
        for e_name, e_value in value_descriptions.items():
            ET.SubElement(
                enum_list,
                "Enumeration",
                attrib={
                    "value": str(e_value),
                    "label": e_name,
                },
            )
    elif data_type.startswith("int") or data_type.startswith("uint"):
        if data_type.startswith("uint"):
            signed = False
            encoding = "unsigned"
            size = data_type[4:]
        else:
            signed = True
            encoding = "twosComplement"
            size = data_type[3:]

        para_type = ET.SubElement(
            root,
            "IntegerParameterType",
            attrib={
                "name": name,
                "signed": str(signed).lower(),
            },
        )

        para_unit_set = ET.SubElement(para_type, "UnitSet")
        if unit:
            para_unit = ET.SubElement(
                para_unit_set,
                "Unit",
            )
            para_unit.text = unit

        data_enc = ET.SubElement(
            para_type,
            "IntegerDataEncoding",
            attrib={
                "byteOrder": "leastSignificantByteFirst",
                "encoding": encoding,
                "sizeInBits": size,
            },
        )
        if factor != 1:
            def_cal = ET.SubElement(data_enc, "DefaultCalibrator")
            poly_cal = ET.SubElement(def_cal, "PolynomialCalibrator")
            ET.SubElement(
                poly_cal,
                "Term",
                attrib={
                    "exponent": "1",
                    "coefficient": str(factor),
                },
            )
    elif data_type == "str":
        para_type = ET.SubElement(
            root,
            "StringParameterType",
            attrib={
                "name": name,
            },
        )
        str_data_enc = ET.SubElement(
            para_type,
            "StringDataEncoding",
            attrib={
                "encoding": "UTF-8",
            },
        )
        size_in_bits = ET.SubElement(str_data_enc, "SizeInBits")
        fixed = ET.SubElement(size_in_bits, "Fixed")
        fixed_value = ET.SubElement(fixed, "FixedValue")
        fixed_value.text = str(len(default) * 8)
    elif data_type == "bytes":
        param_type = ET.SubElement(
            root,
            "BinaryParameterType",
            attrib={
                "name": name,
            },
        )
        if description:
            param_type.attrib["shortDescription"] = description
        ET.SubElement(param_type, "UnitSet")
        bin_data_enc = ET.SubElement(
            param_type, "BinaryDataEncoding", attrib={"bitOrder": "leastSignificantBitFirst"}
        )
        size_in_bits = ET.SubElement(
            bin_data_enc,
            "SizeInBits",
        )
        if size_prefix != 0:
            dyn_val = ET.SubElement(
                size_in_bits,
                "DynamicValue",
            )
            ET.SubElement(
                dyn_val,
                "ParameterInstanceRef",
                attrib={"parameterRef": param_ref},
            )
        else:
            bin_data_enc_size_fixed = ET.SubElement(
                size_in_bits,
                "FixedValue",
            )
            bin_data_enc_size_fixed.text = str(len(default))
    elif data_type == "unix_time":
        para_type = ET.SubElement(
            root,
            "AbsoluteTimeParameterType",
            attrib={
                "name": "unix_time_type",
                "shortDescription": "Unix coarse timestamp",
            },
        )
        enc = ET.SubElement(para_type, "Encoding")
        ET.SubElement(
            enc,
            "IntegerDataEncoding",
            attrib={
                "byteOrder": "leastSignificantByteFirst",
                "sizeInBits": "32",
            },
        )
        ref_time = ET.SubElement(para_type, "ReferenceTime")
        epoch = ET.SubElement(ref_time, "Epoch")
        epoch.text = "1970-01-01T00:00:00.000"
    else:
        raise ValueError(f"data type {data_type} not implemented")


def _add_parameter(para_set: ET.Element, name: str, type_ref: str, description: str = ""):
    para = ET.SubElement(
        para_set,
        "Parameter",
        attrib={
            "name": name,
            "parameterTypeRef": type_ref,
        },
    )
    if description:
        para.attrib["shortDescription"] = description


def _add_parameter_ref(entry_list: ET.Element, name: str) -> ET.Element:
    return ET.SubElement(
        entry_list,
        "ParameterRefEntry",
        attrib={
            "parameterRef": name,
        },
    )


def _add_argument_type(arg_type_set: ET.Element, req_field: EdlCommandField, type_name: str):
    attrib = {
        "name": type_name,
    }

    if req_field.data_type.startswith("int") or req_field.data_type.startswith("uint"):
        if req_field.enums:
            name = "EnumeratedArgumentType"
        else:
            name = "IntegerArgumentType"
    elif req_field.data_type == "bool":
        name = "BooleanArgumentType"
        if req_field.enums:
            attrib["zeroStringValue"] = list(req_field.enums.keys())[
                list(req_field.enums.values()).index(0)
            ]
            attrib["oneStringValue"] = list(req_field.enums.keys())[
                list(req_field.enums.values()).index(1)
            ]
    elif req_field.data_type in ["float32", "float64"]:
        name = "FloatArgumentType"
    elif req_field.data_type == "str":
        name = "StringArgumentType"
    elif req_field.data_type == "bytes":
        name = "BinaryArgumentType"
    else:
        raise ValueError(f"invalid data type {req_field.data_type}")

    data_type = ET.SubElement(arg_type_set, name, attrib=attrib)
    arg_unit_set = ET.SubElement(data_type, "UnitSet")
    if req_field.unit:
        unit = ET.SubElement(
            arg_unit_set,
            "Unit",
        )
        unit.text = req_field.unit

    if req_field.data_type.startswith("int") or req_field.data_type.startswith("uint"):
        size = req_field.data_type.split("int")[-1]
        encoding = "twosComplement" if req_field.data_type.startswith("int") else "unsigned"
        ET.SubElement(
            data_type,
            "IntegerDataEncoding",
            attrib={"sizeInBits": size, "encoding": encoding},
        )

        if req_field.enums:
            enum_list = ET.SubElement(data_type, "EnumerationList")
            for k, v in req_field.enums.items():
                ET.SubElement(
                    enum_list,
                    "Enumeration",
                    attrib={"value": str(v), "label": k},
                )
    elif req_field.data_type == "bool":
        ET.SubElement(
            data_type,
            "IntegerDataEncoding",
            attrib={"sizeInBits": "8", "encoding": "unsigned"},
        )
    elif req_field.data_type in ["float32", "float64"]:
        ET.SubElement(data_type, "FloatDataEncoding")
    elif req_field.data_type == "str":
        str_data = ET.SubElement(
            data_type,
            "StringDataEncoding",
            attrib={"encoding": "US-ASCII", "bitOrder": "mostSignificantBitFirst"},
        )
        if req_field.max_size > 0:
            var = ET.SubElement(
                str_data,
                "Variable",
                attrib={"maxSizeInBits": f"{req_field.max_size * 8}"},
            )
            dyn_val = ET.SubElement(var, "DynamicValue")
            ET.SubElement(
                dyn_val,
                "ArgumentInstanceRef",
                attrib={"argumentRef": f"{req_field.name}_size"},
            )
        elif req_field.fixed_size > 0:
            size_bits = ET.SubElement(str_data, "SizeInBits")
            fixed_value = ET.SubElement(size_bits, "FixedValue")
            fixed_value.text = f"{req_field.fixed_size * 8}"
    elif req_field.data_type == "bytes":
        bytes_data = ET.SubElement(
            data_type,
            "BinaryDataEncoding",
            attrib={"bitOrder": "mostSignificantBitFirst"},
        )
        size_bits = ET.SubElement(bytes_data, "SizeInBits")
        if req_field.size_prefix:
            dyn_val = ET.SubElement(size_bits, "DynamicValue")
            ET.SubElement(
                dyn_val,
                "ArgumentInstanceRef",
                attrib={"argumentRef": f"{req_field.name}_size"},
            )
        elif req_field.fixed_size > 0:
            fixed_value = ET.SubElement(size_bits, "FixedValue")
            fixed_value.text = f"{req_field.fixed_size * 8}"
