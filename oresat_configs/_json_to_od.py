from typing import List, Dict
from dataclasses import dataclass, field

import canopen
from dataclasses_json import dataclass_json, LetterCase

from . import Index

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
    "float32": 0,
    "float64": 0,
    "str": "",
    "octet_str": b"",
    "domain": None,
}


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OdConfigEntry:
    name: str
    """Name of the Entry in snake_case"""
    data_type: str
    """Data type of the entry"""
    description: str = ""
    """Description of the entry"""
    access_type: str = "rw"
    """Access type of the entry; can be: rw, ro, wo, or const"""


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OdConfigPublish:
    fields: List[str]
    """Fields to publish, must match names of entries"""
    delay_ms: int = 0
    """
    Delay between publishing in milliseconds, if both delay_ms and sync are non-zero delay_ms
    is ignored and sync is used.
    """
    sync: int = 0
    """Number of sync messages required before publishing data"""


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OdConfig:
    objects: List[OdConfigEntry]
    """List of objects/entries in OD"""
    publish: Dict[str, OdConfigPublish] = field(default_factory=dict)
    """Publish data configs"""


def make_rec(objects: list, index: int, name: str) -> canopen.objectdictionary.Record:
    rec = canopen.objectdictionary.Record(name, index)

    for obj in objects:
        subindex = objects.index(obj) + 1
        var = canopen.objectdictionary.Variable(obj.name, index, subindex)
        var.access_type = obj.access_type
        var.storage_location = "RAM"
        var.data_type = OD_DATA_TYPES[obj.data_type]
        var.default = OD_DEFAULTS[obj.data_type]
        var.description = obj.description
        rec.add_member(var)

    # index 0
    var = canopen.objectdictionary.Variable("Highest index supported", index, 0x0)
    var.access_type = "const"
    var.storage_location = "RAM"
    var.data_type = canopen.objectdictionary.UNSIGNED8
    var.default = len(rec)
    rec.add_member(var)

    return rec


def add_publish_data(od: canopen.ObjectDictionary, config: OdConfig, core=True):
    if core:
        mapped_index = Index.CORE_DATA.value
    else:
        mapped_index = Index.CARD_DATA.value

    for i in config.publish:
        num = int(i, 16)
        com_index = 0x1800 + num
        map_index = 0x1A00 + num
        com_rec = canopen.objectdictionary.Record(
            f"Publish data {num} communication parameters", com_index
        )
        map_rec = canopen.objectdictionary.Record(
            f"Publish data {num} mapping parameters", map_index
        )
        od.add_object(map_rec)
        od.add_object(com_rec)

        for j in config.publish[i].fields:
            subindex = config.publish[i].fields.index(j) + 1
            var = canopen.objectdictionary.Variable(
                f"Mapping object {subindex}", map_index, subindex
            )
            var.access_type = "const"
            var.storage_location = "RAM"
            var.data_type = canopen.objectdictionary.UNSIGNED32
            mapped_subindex = od[mapped_index][j].subindex
            value = mapped_index << 16
            value += mapped_subindex << 8
            var.default = value
            map_rec.add_member(var)

        # index 0 for mapping index
        var = canopen.objectdictionary.Variable("Highest index supported", map_index, 0x0)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = len(map_rec)
        map_rec.add_member(var)

        var = canopen.objectdictionary.Variable("COB-ID", com_index, 0x1)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED32
        var.default = od.node_id + (num * 0x100) + 0x180
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Transmission type", com_index, 0x2)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        if config.publish[i].sync != 0:
            var.default = config.publish[i].sync
        else:
            var.default = 254
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Inhibit time", com_index, 0x3)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = 0
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Compatibility entry", com_index, 0x4)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Event timer", com_index, 0x5)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = config.publish[i].delay_ms
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("SYNC start value", com_index, 0x6)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        com_rec.add_member(var)

        # index 0 for comms index
        var = canopen.objectdictionary.Variable("Highest index supported", com_index, 0x0)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = len(com_rec)
        com_rec.add_member(var)


def add_all_subscribe_data(
    master_node_od: canopen.ObjectDictionary, node_od: canopen.ObjectDictionary
):
    if (
        0x1800 not in node_od
        and 0x1801 not in node_od
        and 0x1802 not in node_od
        and 0x1803 not in node_od
    ):
        return

    node_name = node_od.device_information.product_name

    node_rec_index = 0x7000 + node_od.node_id
    if node_rec_index not in master_node_od:
        node_rec = canopen.objectdictionary.Record(f"{node_name}", node_rec_index)
        master_node_od.add_object(node_rec)

        # index 0 for node data index
        var = canopen.objectdictionary.Variable("Highest index supported", node_rec_index, 0x0)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        node_rec.add_member(var)

    for i in range(4):
        if i + 0x1800 not in node_od:
            continue

        com_index = 0x1400 + (i * 0x80) + node_od.node_id
        com_rec = canopen.objectdictionary.Record(
            f"Subscribe {node_name} data communication parameters", com_index
        )
        master_node_od.add_object(com_rec)

        var = canopen.objectdictionary.Variable("COB-ID", com_index, 0x1)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED32
        var.default = node_od.node_id + (i * 0x100) + 0x180
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Transmission type", com_index, 0x2)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 254
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Inhibit time", com_index, 0x3)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = 0
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Compatibility entry", com_index, 0x4)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("Event timer", com_index, 0x5)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = 0
        com_rec.add_member(var)

        var = canopen.objectdictionary.Variable("SYNC start value", com_index, 0x6)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        com_rec.add_member(var)

        # index 0 for comms index
        var = canopen.objectdictionary.Variable("Highest index supported", com_index, 0x0)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = len(com_rec)
        com_rec.add_member(var)

        map_index = 0x1600 + (i * 0x80) + node_od.node_id
        map_rec = canopen.objectdictionary.Record(
            f"Subscribe {node_name} data mapping parameters", map_index
        )
        master_node_od.add_object(map_rec)

        # index 0 for map index
        var = canopen.objectdictionary.Variable("Highest index supported", map_index, 0x0)
        var.access_type = "const"
        var.storage_location = "RAM"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        map_rec.add_member(var)

        node_map_index = 0x1A00 + i
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
            var.storage_location = "RAM"
            var.data_type = node_obj.data_type
            var.default = node_obj.default
            node_rec.add_member(var)

            # master node mapping obj
            map_rec_subindex = map_rec[0].default + 1
            var = canopen.objectdictionary.Variable(
                f"Mapping object {map_rec_subindex}", map_index, map_rec_subindex
            )
            var.access_type = "const"
            var.storage_location = "RAM"
            var.data_type = canopen.objectdictionary.UNSIGNED32
            value = node_map_index << 16
            value += node_rec_subindex << 8
            var.default = value
            map_rec.add_member(var)

            # update these
            node_rec[0].default += 1
            map_rec[0].default += 1


def read_json_od_config(file_path):
    with open(file_path, "r") as f:
        config = f.read()

    return OdConfig.from_json(config)


def make_od(config, node_id, core_config=None):
    od = canopen.ObjectDictionary()
    od.bitrate = 1_000_000
    od.node_id = node_id.value
    od.device_information.product_name = node_id.name.lower()

    if core_config:
        core_rec = make_rec(core_config.objects, Index.CORE_DATA, "core")
        od.add_object(core_rec)
        add_publish_data(od, core_config)

    card_rec = make_rec(config.objects, Index.CARD_DATA, node_id.name.lower())
    od.add_object(card_rec)
    add_publish_data(od, config, False)

    return od
