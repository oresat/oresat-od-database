"""Convert OreSat JSON files to an canopen.ObjectDictionary object."""

from dataclasses import dataclass, field
from typing import List, Dict, Any

import canopen
from dataclasses_json import dataclass_json, LetterCase

from . import __version__, Index, NodeId

RPDO_COMM_START = 0x1400
RPDO_PARA_START = 0x1600
TPDO_COMM_START = 0x1800
TPDO_PARA_START = 0x1A00

OD_DATA_TYPES = {
    "bool": canopen.objectdictionary.BOOLEAN,
    "int8": canopen.objectdictionary.INTEGER8,
    "int16": canopen.objectdictionary.INTEGER16,
    "int32": canopen.objectdictionary.INTEGER32,
    "int64": canopen.objectdictionary.INTEGER64,
    "uint8": canopen.objectdictionary.UNSIGNED8,
    "uint16": canopen.objectdictionary.UNSIGNED16,
    "uint32": canopen.objectdictionary.UNSIGNED32,
    "uint64": canopen.objectdictionary.UNSIGNED64,
    "float32": canopen.objectdictionary.REAL32,
    "float64": canopen.objectdictionary.REAL64,
    "str": canopen.objectdictionary.VISIBLE_STRING,
    "octet_str": canopen.objectdictionary.OCTET_STRING,
    "domain": canopen.objectdictionary.DOMAIN,
}

OD_DATA_TYPE_SIZE = {
    canopen.objectdictionary.BOOLEAN: 8,
    canopen.objectdictionary.INTEGER8: 8,
    canopen.objectdictionary.INTEGER16: 16,
    canopen.objectdictionary.INTEGER32: 32,
    canopen.objectdictionary.INTEGER64: 64,
    canopen.objectdictionary.UNSIGNED8: 8,
    canopen.objectdictionary.UNSIGNED16: 16,
    canopen.objectdictionary.UNSIGNED32: 32,
    canopen.objectdictionary.UNSIGNED64: 64,
    canopen.objectdictionary.REAL32: 32,
    canopen.objectdictionary.REAL64: 64,
    canopen.objectdictionary.VISIBLE_STRING: 0,
    canopen.objectdictionary.OCTET_STRING: 0,
    canopen.objectdictionary.DOMAIN: 0,
}

OD_DEFAULTS = {
    "bool": False,
    "int8": 0,
    "int16": 0,
    "int32": 0,
    "int64": 0,
    "uint8": 0,
    "uint16": 0,
    "uint32": 0,
    "uint64": 0,
    "float32": 0.0,
    "float64": 0.0,
    "str": "",
    "octet_str": b"",
    "domain": None,
}


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OdConfigEntry:
    """OD entry info."""

    name: str
    """Name of the entry in snake_case."""
    data_type: str
    """Data type of the entry."""
    description: str = ""
    """Description of the entry."""
    access_type: str = "rw"
    """Access type of the entry; can be: ro, wo, rw, rwr, rww, or const."""
    default: Any = None
    """Optional default value of the entry. If not set, value from OD_DEFAULTS is used."""


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OdConfigRpdo:
    """TPDO info to build RPDO data from."""

    card: str
    """Card the TPDO is from."""
    tpdo_num: int
    """TPDO number."""


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OdConfigTpdo:
    """TPDO data."""

    fields: List[str]
    """Fields to tpdos, must match names of entries."""
    delay_ms: int = 0
    """
    Delay between tpdosing in milliseconds, if both delay_ms and sync are non-zero delay_ms
    is ignored and sync is used.
    """
    sync: int = 0
    """Number of sync messages required before sending TPDO message."""


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OdConfig:
    """OD data info."""

    objects: List[OdConfigEntry]
    """List of objects/entries in OD."""
    tpdos: Dict[str, OdConfigTpdo] = field(default_factory=dict)
    """TPDO configs."""
    rpdos: Dict[str, OdConfigRpdo] = field(default_factory=dict)
    """RPDO configs."""


def _add_rec(
    od: canopen.ObjectDictionary, objects: list, index: Index
) -> canopen.objectdictionary.Record:
    """Add a Record tothe OD based off the config objects."""

    rec = canopen.objectdictionary.Record(index.name.lower(), index.value)

    for obj in objects:
        subindex = objects.index(obj) + 1
        var = canopen.objectdictionary.Variable(obj.name, index, subindex)
        var.access_type = obj.access_type
        var.data_type = OD_DATA_TYPES[obj.data_type]
        if obj.name == "config_version":
            var.default = __version__
        elif obj.default is None:
            var.default = OD_DEFAULTS[obj.data_type]
        else:
            var.default = obj.default
        var.description = obj.description
        rec.add_member(var)

    # index 0
    var = canopen.objectdictionary.Variable("Highest index supported", index, 0x0)
    var.access_type = "const"
    var.data_type = canopen.objectdictionary.UNSIGNED8
    var.default = len(rec)
    rec.add_member(var)

    od.add_object(rec)


def _add_tpdo_data(od: canopen.ObjectDictionary, config: OdConfig):
    """Add tpdo objects to OD."""

    for i in config.tpdos:
        od.device_information.nr_of_TXPDO += 1

        num = int(i)
        com_index = TPDO_COMM_START + num - 1
        map_index = TPDO_PARA_START + num - 1
        com_rec = canopen.objectdictionary.Record(
            f"TPDO {num} communication parameters", com_index
        )
        map_rec = canopen.objectdictionary.Record(f"TPDO {num} mapping parameters", map_index)
        od.add_object(map_rec)
        od.add_object(com_rec)

        for j in config.tpdos[i].fields:
            subindex = config.tpdos[i].fields.index(j) + 1
            var = canopen.objectdictionary.Variable(
                f"Mapping object {subindex}", map_index, subindex
            )
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED32
            try:
                mapped_obj = od[Index.CARD_DATA.value][j]
            except KeyError:
                mapped_obj = od[Index.CORE_DATA.value][j]
            mapped_subindex = mapped_obj.subindex
            value = mapped_obj.index << 16
            value += mapped_subindex << 8
            value += OD_DATA_TYPE_SIZE[mapped_obj.data_type]
            var.default = value
            map_rec.add_member(var)

        # index 0 for mapping index
        var = canopen.objectdictionary.Variable("Highest index supported", map_index, 0x0)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = len(map_rec)
        map_rec.add_member(var)

        var = canopen.objectdictionary.Variable("COB-ID", com_index, 0x1)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED32
        node_id = od.node_id
        if od.node_id == NodeId.GPS and num == 16:
            # time sync TPDO from GPS uses C3 TPDO 1
            node_id = NodeId.C3.value
            num = 1
        var.default = node_id + (((num - 1) % 4) * 0x100) + 0x180
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Transmission type", com_index, 0x2)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        if config.tpdos[i].sync != 0:
            var.default = config.tpdos[i].sync
        else:
            var.default = 255  # event driven (delay-based or app specific)
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Inhibit time", com_index, 0x3)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = 0
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Compatibility entry", com_index, 0x4)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Event timer", com_index, 0x5)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = config.tpdos[i].delay_ms
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("SYNC start value", com_index, 0x6)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        com_rec.add_member(var)

        # index 0 for comms index
        var = canopen.objectdictionary.Variable("Highest index supported", com_index, 0x0)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = len(com_rec)
        com_rec.add_member(var)


def add_all_rpdo_data(master_node_od: canopen.ObjectDictionary, node_od: canopen.ObjectDictionary):
    """Add all RPDO object to OD based off of TPDO objects from another OD."""

    if not node_od.device_information.nr_of_TXPDO:
        return  # no TPDOs

    node_name = node_od.device_information.product_name

    node_rec_index = Index._OTHER_CARD_BASE_INDEX + node_od.node_id
    if node_rec_index not in master_node_od:
        node_rec = canopen.objectdictionary.Record(f"{node_name}_data", node_rec_index)
        master_node_od.add_object(node_rec)

        # index 0 for node data index
        var = canopen.objectdictionary.Variable("Highest index supported", node_rec_index, 0x0)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        node_rec.add_member(var)

    for i in range(16):
        if i + TPDO_COMM_START not in node_od:
            continue

        master_node_od.device_information.nr_of_RXPDO += 1
        rpdo_num = master_node_od.device_information.nr_of_RXPDO

        com_index = RPDO_COMM_START + rpdo_num - 1
        com_rec = canopen.objectdictionary.Record(
            f"RPDO {rpdo_num} communication parameters", com_index
        )
        master_node_od.add_object(com_rec)

        var = canopen.objectdictionary.Variable("COB-ID", com_index, 0x1)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED32
        var.default = node_od[i + 0x1800][0x1].default  # get value from TPDO def
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Transmission type", com_index, 0x2)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 255
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Event timer", com_index, 0x5)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = 0
        com_rec.add_member(var)

        # index 0 for comms index
        var = canopen.objectdictionary.Variable("Highest index supported", com_index, 0x0)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = sorted([k for k in com_rec.subindices.keys()])[-1]  # no subindex 0x3 and 0x4
        com_rec.add_member(var)

        map_index = RPDO_PARA_START + rpdo_num - 1
        map_rec = canopen.objectdictionary.Record(f"RPDO {rpdo_num} mapping parameters", map_index)
        master_node_od.add_object(map_rec)

        # index 0 for map index
        var = canopen.objectdictionary.Variable("Highest index supported", map_index, 0x0)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        map_rec.add_member(var)

        node_map_index = TPDO_PARA_START + i
        for j in range(len(node_od[node_map_index])):
            if j == 0:
                continue  # skip

            node_obj = node_od[node_map_index][j]

            # master node data
            node_rec_subindex = node_rec[0].default + 1
            mapped_index = (node_obj.default >> 16) & 0xFFFF
            mapped_subindex = (node_obj.default >> 8) & 0xFF
            mapped_obj = node_od[mapped_index][mapped_subindex]
            var = canopen.objectdictionary.Variable(
                mapped_obj.name, node_rec_index, node_rec_subindex
            )
            var.access_type = "const"
            var.data_type = mapped_obj.data_type
            var.default = mapped_obj.default
            node_rec.add_member(var)

            # master node mapping obj
            map_rec_subindex = map_rec[0].default + 1
            var = canopen.objectdictionary.Variable(
                f"Mapping object {map_rec_subindex}", map_index, map_rec_subindex
            )
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED32
            value = node_rec_index << 16
            value += node_rec_subindex << 8
            value += OD_DATA_TYPE_SIZE[master_node_od[node_rec_index][node_rec_subindex].data_type]
            var.default = value
            map_rec.add_member(var)

            # update these
            node_rec[0].default += 1
            map_rec[0].default += 1


def read_json_od_config(file_path: str) -> OdConfig:
    """read the od JSON in."""

    with open(file_path, "r") as f:
        config = f.read()

    return OdConfig.from_json(config)


def make_od(
    node_id: NodeId, card_config: OdConfig, core_config: OdConfig, add_core_tpdos: bool = True
) -> canopen.ObjectDictionary:
    """Make the OD from a config."""

    od = canopen.ObjectDictionary()
    od.bitrate = 1_000_000  # bps
    od.node_id = node_id.value
    od.device_information.allowed_baudrates = set([1000])
    od.device_information.vendor_name = "PSAS"
    od.device_information.vendor_number = 0
    od.device_information.product_name = node_id.name.lower()
    od.device_information.product_number = 0
    od.device_information.revision_number = 0
    od.device_information.order_code = 0
    od.device_information.simple_boot_up_master = False
    od.device_information.simple_boot_up_slave = False
    od.device_information.granularity = 8
    od.device_information.dynamic_channels_supported = False
    od.device_information.group_messaging = False
    od.device_information.nr_of_RXPDO = 0
    od.device_information.nr_of_TXPDO = 0
    od.device_information.LSS_supported = False

    _add_rec(od, core_config.objects, Index.CORE_DATA)
    if add_core_tpdos:
        _add_tpdo_data(od, core_config)

    _add_rec(od, card_config.objects, Index.CARD_DATA)
    _add_tpdo_data(od, card_config)

    return od
