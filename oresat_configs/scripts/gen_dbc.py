"""Generate a DBC file for SavvyCAN."""

from argparse import ArgumentParser, Namespace
from typing import Optional

from canopen.objectdictionary import UNSIGNED_TYPES, Variable

from .. import Consts, OreSatConfig

GEN_DBC = "generate dbc file for SavvyCAN"

VECTOR = "Vector__XXX"  # flag for default, any, all devices
INDENT3 = " " * 3
INDENT4 = " " * 4
CANOPEN_STATES = {
    0x00: "BOOT UP",
    0x04: "STOPPED",
    0x05: "OPERATIONAL",
    0x7F: "PRE-OPERATIONAL",
}


def build_parser(parser: ArgumentParser) -> ArgumentParser:
    """Configures an ArgumentParser suitable for this script.

    The given parser may be standalone or it may be used as a subcommand in another ArgumentParser.
    """
    parser.description = GEN_DBC
    parser.add_argument(
        "--oresat",
        default=Consts.default().arg,
        choices=[m.arg for m in Consts],
        type=lambda x: x.lower().removeprefix("oresat"),
        help="oresat mission, defaults to %(default)s",
    )
    parser.add_argument("-d", "--dir-path", default=".", help='directory path; defautl "."')
    return parser


def register_subparser(subparsers):
    """Registers an ArgumentParser as a subcommand of another parser.

    Intended to be called by __main__.py for each script. Given the output of add_subparsers(),
    (which I think is a subparser group, but is technically unspecified) this function should
    create its own ArgumentParser via add_parser(). It must also set_default() the func argument
    to designate the entry point into this script.
    See https://docs.python.org/3/library/argparse.html#sub-commands, especially the end of that
    section, for more.
    """
    parser = build_parser(subparsers.add_parser("dbc", help=GEN_DBC))
    parser.set_defaults(func=gen_dbc)


def write_dbc(config: OreSatConfig, dir_path: str = "."):
    """Write beacon configs to a xtce file."""

    file_name = config.mission.name.lower().replace(".", "_") + ".dbc"
    if dir_path:
        file_path = f"{dir_path}/{file_name}"
    else:
        file_path = file_name

    lines = [
        'VERSION ""',
        "",
        "",
        "NS_ :",
        f"{INDENT4}NS_DESC_",
        f"{INDENT4}CM_",
        f"{INDENT4}BA_DEF_",
        f"{INDENT4}BA_",
        f"{INDENT4}VAL_",
        f"{INDENT4}CAT_DEF_",
        f"{INDENT4}CAT_",
        f"{INDENT4}FILTER_",
        f"{INDENT4}BA_DEF_DEF_",
        f"{INDENT4}EV_DATA_",
        f"{INDENT4}ENVVAR_DATA_",
        f"{INDENT4}SGTYPE_",
        f"{INDENT4}SGTYPE_VAL_",
        f"{INDENT4}BA_DEF_SGTYPE_",
        f"{INDENT4}BA_SGTYPE_",
        f"{INDENT4}SIG_TYPE_REG_",
        f"{INDENT4}VAL_TABLE_",
        f"{INDENT4}SIG_GROUP_",
        f"{INDENT4}SIG_VALTYPE_",
        f"{INDENT4}SIGTYPE_VALTYPE_",
        f"{INDENT4}BO_TX_BU_",
        f"{INDENT4}BA_DEF_REL_",
        f"{INDENT4}BA_REL_",
        f"{INDENT4}BA_DEF_DEF_REL_",
        f"{INDENT4}BU_SG_REL_",
        f"{INDENT4}BU_EV_REL_",
        f"{INDENT4}BU_BO_REL_",
        f"{INDENT4}SG_MUL_VAL_",
        "",
        "BS_:",
    ]

    # list of cards
    cards = config.cards
    lines.append("BU_:" + " ".join(cards))

    # SYNC
    lines.append(f"BO_ {0x80} sync: 0 c3")
    lines.append("")

    datatypes = []
    for name, od in config.od_db.items():
        if name not in cards:
            continue

        # EMCYs
        cob_id = 0x80 + od.node_id
        lines.append(f"BO_ {cob_id} {name}_emcy: 8 {name}")
        lines.append(f'{INDENT3}SG_ emcy_code : 0|16@1+ (1,0) [0|0] "" {VECTOR}')
        lines.append(f'{INDENT3}SG_ emcy_code2 : 16|8@1+ (1,0) [0|0] "" {VECTOR}')
        lines.append(f'{INDENT3}SG_ emcy_data : 24|40@1+ (1,0) [0|0] "" {VECTOR}')
        lines.append("")

        # TPDOs
        for param_index in od:
            if param_index < 0x1800 or param_index >= 0x1A00:
                continue
            if param_index not in od:
                continue
            tpdo_lines = []
            mapping_index = param_index + 0x200
            tpdo = param_index - 0x1800 + 1
            cob_id = od[param_index][1].value
            sb = 0
            if name == "gps" and cob_id == 0x181:
                continue  # time sync tpdo, both c3 and gps can send this, skip for gps
            for subindex in od[mapping_index].subindices:
                val = od[mapping_index][subindex].default
                mapped_index = (val >> 16) & 0xFFFF
                mapped_subindex = (val >> 8) & 0xFF
                mapped_size = val & 0xFF
                if subindex == 0:
                    continue
                if isinstance(od[mapped_index], Variable):
                    obj = od[mapped_index]
                    signal = obj.name
                else:
                    obj = od[mapped_index][mapped_subindex]
                    signal = obj.parent.name + "_" + obj.name
                sign = "+" if obj.data_type in UNSIGNED_TYPES else "-"
                low = obj.min if obj.min is not None else 0
                high = obj.max if obj.max is not None else 0
                tpdo_lines.append(
                    f"{INDENT3}SG_ {signal} : {sb}|{mapped_size}@1{sign} ({obj.factor},0) "
                    f'[{low}|{high}] "{obj.unit}" {VECTOR}'
                )
                sb += mapped_size
            size = sb // 8
            lines.append(f"BO_ {cob_id} {name}_tpdo_{tpdo}: {size} {name}")
            lines += tpdo_lines
            lines.append("")

        # SDOs
        if name != "c3":
            cob_id = 0x580 + od.node_id
            lines.append(f"BO_ {cob_id} {name}_sdo_tx: 8 c3")
            lines.append(f'{INDENT3}SG_ sdo_tx_data : 0|64@1+ (1,0) [0|0] "" {name}')
            lines.append("")

            cob_id = 0x600 + od.node_id
            lines.append(f"BO_ {cob_id} {name}_sdo_rx: 8 {name}")
            lines.append(f'{INDENT3}SG_ sdo_rx_data : 0|64@1+ (1,0) [0|0] "" c3')
            lines.append("")

        # heartbeats
        cob_id = 0x700 + od.node_id
        lines.append(f"BO_ {cob_id} {name}_heartbeat: 1 {name}")
        lines.append(f'{INDENT3}SG_ hearbeat : 0|8@1+ (1,0) [0|0] "" c3')
        datatypes.append((cob_id, "hearbeat", CANOPEN_STATES))
        lines.append("")

    # custom datatypes
    for i in datatypes:
        line = f"VAL_ {i[0]} {i[1]}"
        for key, value in i[2].items():
            line += f' {key} "{value}"'
        line += ";"
        lines.append(line)

    with open(file_path, "w") as f:
        for line in lines:
            f.write(line + "\n")


def gen_dbc(args: Optional[Namespace] = None):
    """Gen_dbc main."""
    if args is None:
        args = build_parser(ArgumentParser()).parse_args()

    config = OreSatConfig(args.oresat)
    write_dbc(config, args.dir_path)
