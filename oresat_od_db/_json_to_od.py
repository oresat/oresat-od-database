"""Convert OreSat JSON files to an canopen.ObjectDictionary object."""

import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List

import canopen
from dataclasses_json import LetterCase, dataclass_json

from . import NODE_NICE_NAMES, Index, NodeId, OreSatId, __version__

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
    canopen.objectdictionary.BOOLEAN: False,
    canopen.objectdictionary.INTEGER8: 0,
    canopen.objectdictionary.INTEGER16: 0,
    canopen.objectdictionary.INTEGER32: 0,
    canopen.objectdictionary.INTEGER64: 0,
    canopen.objectdictionary.UNSIGNED8: 0,
    canopen.objectdictionary.UNSIGNED16: 0,
    canopen.objectdictionary.UNSIGNED32: 0,
    canopen.objectdictionary.UNSIGNED64: 0,
    canopen.objectdictionary.REAL32: 0.0,
    canopen.objectdictionary.REAL64: 0.0,
    canopen.objectdictionary.VISIBLE_STRING: "",
    canopen.objectdictionary.OCTET_STRING: b"",
    canopen.objectdictionary.DOMAIN: None,
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

    std_objects: List[str] = field(default_factory=list)
    """List of standard object to add."""
    objects: List[OdConfigEntry] = field(default_factory=list)
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

    dynamic_len_data_types = [
        canopen.objectdictionary.VISIBLE_STRING,
        canopen.objectdictionary.OCTET_STRING,
        canopen.objectdictionary.DOMAIN,
    ]

    for obj in objects:
        subindex = objects.index(obj) + 1
        var = canopen.objectdictionary.Variable(obj.name, index, subindex)
        var.access_type = obj.access_type
        var.data_type = OD_DATA_TYPES[obj.data_type]
        if obj.name == "db_version":
            var.default = __version__
        elif obj.default is None:
            var.default = OD_DEFAULTS[var.data_type]
        elif var.data_type in canopen.objectdictionary.INTEGER_TYPES and isinstance(
            obj.default, str
        ):  # fix hex values data types
            var.default = int(obj.default, 16)
        else:
            var.default = obj.default
        var.description = obj.description
        if var.data_type not in dynamic_len_data_types:
            var.pdo_mappable = True
        rec.add_member(var)

    # index 0
    var = canopen.objectdictionary.Variable("highest_index_supported", index, 0x0)
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
        comm_index = TPDO_COMM_START + num - 1
        map_index = TPDO_PARA_START + num - 1
        comm_rec = canopen.objectdictionary.Record(
            f"tpdo_{num}_communication_parameters", comm_index
        )
        map_rec = canopen.objectdictionary.Record(f"tpdo_{num}_mapping_parameters", map_index)
        od.add_object(map_rec)
        od.add_object(comm_rec)

        for j in config.tpdos[i].fields:
            subindex = config.tpdos[i].fields.index(j) + 1
            var = canopen.objectdictionary.Variable(
                f"mapping_object_{subindex}", map_index, subindex
            )
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED32
            if config.tpdos[i].fields[subindex - 1] == "scet":
                mapped_obj = od[Index.SCET.value]
            else:
                try:
                    mapped_obj = od[Index.CARD_DATA.value][j]
                except KeyError:
                    mapped_obj = od[Index.COMMON_DATA.value][j]
            mapped_subindex = mapped_obj.subindex
            value = mapped_obj.index << 16
            value += mapped_subindex << 8
            value += OD_DATA_TYPE_SIZE[mapped_obj.data_type]
            var.default = value
            map_rec.add_member(var)

        # index 0 for mapping index
        var = canopen.objectdictionary.Variable("highest_index_supported", map_index, 0x0)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = len(map_rec)
        map_rec.add_member(var)

        var = canopen.objectdictionary.Variable("cob_id", comm_index, 0x1)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED32
        node_id = od.node_id
        if od.node_id == NodeId.GPS and num == 16:
            # time sync TPDO from GPS uses C3 TPDO 1
            node_id = NodeId.C3.value
            num = 1
        var.default = node_id + (((num - 1) % 4) * 0x100) + ((num - 1) // 4) + 0x180
        comm_rec.add_member(var)

        var = canopen.objectdictionary.Variable("transmission_type", comm_index, 0x2)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        if config.tpdos[i].sync != 0:
            var.default = config.tpdos[i].sync
        else:
            var.default = 255  # event driven (delay-based or app specific)
        comm_rec.add_member(var)

        var = canopen.objectdictionary.Variable("inhibit_time", comm_index, 0x3)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = 0
        comm_rec.add_member(var)

        var = canopen.objectdictionary.Variable("compatibility_entry", comm_index, 0x4)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        comm_rec.add_member(var)

        var = canopen.objectdictionary.Variable("event_timer", comm_index, 0x5)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED16
        var.default = config.tpdos[i].delay_ms
        comm_rec.add_member(var)

        var = canopen.objectdictionary.Variable("sync_start_value", comm_index, 0x6)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = 0
        comm_rec.add_member(var)

        # index 0 for comms index
        var = canopen.objectdictionary.Variable("highest_index_supported", comm_index, 0x0)
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED8
        var.default = len(comm_rec)
        comm_rec.add_member(var)


def _add_rpdo_data(
    tpdo_num: int, rpdo_node_od: canopen.ObjectDictionary, tpdo_node_od: canopen.ObjectDictionary
):
    node_name = NodeId(tpdo_node_od.node_id).name.lower()
    tpdo_comm_index = TPDO_COMM_START + tpdo_num - 1
    tpdo_mapping_index = TPDO_PARA_START + tpdo_num - 1

    time_sync_tpdo = tpdo_node_od[tpdo_comm_index]["cob_id"].default == 0x181
    if time_sync_tpdo:
        rpdo_mapped_index = Index.SCET.value
        rpdo_mapped_rec = rpdo_node_od[rpdo_mapped_index]
        rpdo_mapped_subindex = 0
    else:
        rpdo_mapped_index = Index.OTHER_CARD_BASE_INDEX + tpdo_node_od.node_id
        if rpdo_mapped_index not in rpdo_node_od:
            rpdo_mapped_rec = canopen.objectdictionary.Record(
                f"{node_name}_data", rpdo_mapped_index
            )
            rpdo_node_od.add_object(rpdo_mapped_rec)

            # index 0 for node data index
            var = canopen.objectdictionary.Variable(
                "highest_index_supported", rpdo_mapped_index, 0x0
            )
            var.access_type = "const"
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.default = 0
            rpdo_mapped_rec.add_member(var)
        else:
            rpdo_mapped_rec = rpdo_node_od[rpdo_mapped_index]

    rpdo_node_od.device_information.nr_of_RXPDO += 1
    rpdo_num = rpdo_node_od.device_information.nr_of_RXPDO

    rpdo_comm_index = RPDO_COMM_START + rpdo_num - 1
    rpdo_comm_rec = canopen.objectdictionary.Record(
        f"rpdo_{rpdo_num}_communication_parameters", rpdo_comm_index
    )
    rpdo_node_od.add_object(rpdo_comm_rec)

    var = canopen.objectdictionary.Variable("cob_id", rpdo_comm_index, 0x1)
    var.access_type = "const"
    var.data_type = canopen.objectdictionary.UNSIGNED32
    var.default = tpdo_node_od[tpdo_comm_index][0x1].default  # get value from TPDO def
    rpdo_comm_rec.add_member(var)

    var = canopen.objectdictionary.Variable("transmission_type", rpdo_comm_index, 0x2)
    var.access_type = "const"
    var.data_type = canopen.objectdictionary.UNSIGNED8
    var.default = 255
    rpdo_comm_rec.add_member(var)

    var = canopen.objectdictionary.Variable("event_timer", rpdo_comm_index, 0x5)
    var.access_type = "const"
    var.data_type = canopen.objectdictionary.UNSIGNED16
    var.default = 0
    rpdo_comm_rec.add_member(var)

    # index 0 for comms index
    var = canopen.objectdictionary.Variable("highest_index_supported", rpdo_comm_index, 0x0)
    var.access_type = "const"
    var.data_type = canopen.objectdictionary.UNSIGNED8
    var.default = sorted(list(rpdo_comm_rec.subindices))[-1]  # no subindex 3 or 4
    rpdo_comm_rec.add_member(var)

    rpdo_mapping_index = RPDO_PARA_START + rpdo_num - 1
    rpdo_mapping_rec = canopen.objectdictionary.Record(
        f"rpdo_{rpdo_num}_mapping_parameters", rpdo_mapping_index
    )
    rpdo_node_od.add_object(rpdo_mapping_rec)

    # index 0 for map index
    var = canopen.objectdictionary.Variable("highest_index_supported", rpdo_mapping_index, 0x0)
    var.access_type = "const"
    var.data_type = canopen.objectdictionary.UNSIGNED8
    var.default = 0
    rpdo_mapping_rec.add_member(var)

    for j in range(len(tpdo_node_od[tpdo_mapping_index])):
        if j == 0:
            continue  # skip

        tpdo_mapping_obj = tpdo_node_od[tpdo_mapping_index][j]

        # master node data
        if not time_sync_tpdo:
            rpdo_mapped_subindex = rpdo_mapped_rec[0].default + 1
            tpdo_mapped_index = (tpdo_mapping_obj.default >> 16) & 0xFFFF
            tpdo_mapped_subindex = (tpdo_mapping_obj.default >> 8) & 0xFF
            tpdo_mapped_obj = tpdo_node_od[tpdo_mapped_index][tpdo_mapped_subindex]
            var = canopen.objectdictionary.Variable(
                tpdo_mapped_obj.name, rpdo_mapped_index, rpdo_mapped_subindex
            )
            var.access_type = "const"
            var.data_type = tpdo_mapped_obj.data_type
            var.default = tpdo_mapped_obj.default
            rpdo_mapped_rec.add_member(var)

        # master node mapping obj
        rpdo_mapping_subindex = rpdo_mapping_rec[0].default + 1
        var = canopen.objectdictionary.Variable(
            f"mapping_object_{rpdo_mapping_subindex}",
            rpdo_mapping_index,
            rpdo_mapping_subindex,
        )
        var.access_type = "const"
        var.data_type = canopen.objectdictionary.UNSIGNED32
        value = rpdo_mapped_index << 16
        value += rpdo_mapped_subindex << 8
        if rpdo_mapped_subindex == 0:
            rpdo_mapped_obj = rpdo_node_od[rpdo_mapped_index]
        else:
            rpdo_mapped_obj = rpdo_node_od[rpdo_mapped_index][rpdo_mapped_subindex]
        value += OD_DATA_TYPE_SIZE[rpdo_mapped_obj.data_type]
        var.default = value
        rpdo_mapping_rec.add_member(var)

        # update these
        if not time_sync_tpdo:
            rpdo_mapped_rec[0].default += 1
        rpdo_mapping_rec[0].default += 1


def _add_node_rpdo_data(config, od: canopen.ObjectDictionary, od_db: dict):
    """Add all configured RPDO object to OD based off of TPDO objects from another OD."""

    for i in config.rpdos:
        rpdo = config.rpdos[i]
        _add_rpdo_data(int(rpdo.tpdo_num), od, od_db[NodeId[rpdo.card.upper()]])


def _add_all_rpdo_data(
    master_node_od: canopen.ObjectDictionary, node_od: canopen.ObjectDictionary
):
    """Add all RPDO object to OD based off of TPDO objects from another OD."""

    if not node_od.device_information.nr_of_TXPDO:
        return  # no TPDOs

    for i in range(1, 17):
        if TPDO_COMM_START + i - 1 not in node_od:
            continue

        _add_rpdo_data(i, master_node_od, node_od)


def read_json_od_config(file_path: str) -> OdConfig:
    """read the od JSON in."""

    with open(file_path, "r") as f:
        config = f.read()

    # pylint: disable=no-member
    return OdConfig.from_json(config)  # type: ignore


def _load_std_objs(file_path: str) -> dict:
    """Load the standard objects."""

    with open(file_path, "r") as f:
        std_objs_raw = json.load(f)

    std_objs = {}
    for key in std_objs_raw:
        obj = std_objs_raw[key]
        index = int(obj["index"], 16)
        if obj["object_type"] == "variable":
            var = canopen.objectdictionary.Variable(key, index, 0x0)
            var.data_type = OD_DATA_TYPES[obj["data_type"]]
            var.access_type = obj.get("access_type", "rw")
            var.default = obj.get("default", OD_DEFAULTS[var.data_type])
            if var.data_type in canopen.objectdictionary.INTEGER_TYPES and isinstance(
                var.default, str
            ):  # fix hex values data types
                if "+$NODE_ID" in var.default:
                    var.default = var.default.split("+")[0]
                elif "$NODE_ID+" in var.default:
                    var.default = var.default.split("+")[1]
                var.default = int(var.default, 16)
            var.description = obj.get("description", "")
            if var.name == "scet":
                var.pdo_mappable = True
            std_objs[key] = var
        elif obj["object_type"] == "record":
            rec = canopen.objectdictionary.Record(key, index)

            var = canopen.objectdictionary.Variable("highest_index_supported", index, 0x0)
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.access_type = "const"
            var.default = 0
            rec.add_member(var)

            for subindex_str in obj["subindexes"]:
                subindex = int(subindex_str, 16)
                sub_obj = obj["subindexes"][subindex_str]
                var = canopen.objectdictionary.Variable(sub_obj["name"], index, subindex)
                var.data_type = OD_DATA_TYPES[sub_obj["data_type"]]
                var.access_type = sub_obj.get("access_type", "rw")
                var.default = sub_obj.get("default", OD_DEFAULTS[var.data_type])
                if var.data_type in canopen.objectdictionary.INTEGER_TYPES and isinstance(
                    var.default, str
                ):  # fix hex values data types
                    var.default = int(var.default, 16)
                var.description = sub_obj.get("description", "")
                rec.add_member(var)

            rec[0].default = subindex
            std_objs[key] = rec
        elif obj["object_type"] == "array":
            arr = canopen.objectdictionary.Array(key, index)
            data_type = OD_DATA_TYPES[obj["data_type"]]
            access_type = obj.get("access_type", "rw")
            default = obj.get("default", OD_DEFAULTS[data_type])
            length = obj["length"]

            var = canopen.objectdictionary.Variable("highest_index_supported", index, 0x0)
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.access_type = "const"
            var.default = length + 1
            arr.add_member(var)

            for subindex in range(1, length + 1):
                var_name = key + f"_{subindex}"
                var = canopen.objectdictionary.Variable(var_name, index, subindex)
                var.data_type = data_type
                var.access_type = access_type
                var.default = default
                arr.add_member(var)

            std_objs[key] = arr
        else:
            raise ValueError(f"unknown object_type for object {key}")

    return std_objs


def gen_od_db(oresat_id: OreSatId, beacon_def: dict, configs: dict) -> dict:
    """Generate all ODs for a OreSat mission."""

    std_objs_file_name = f"{os.path.dirname(os.path.abspath(__file__))}/standard_objects.json"
    std_objs = _load_std_objs(std_objs_file_name)

    od_db = {}

    # don't apply overlays to original configs
    configs = deepcopy(configs)

    # make od with common and card objects and tpdos
    for node_id in configs:
        card_config = configs[node_id][0]
        common_config = configs[node_id][1]

        # deal with overlays
        if len(configs[node_id]) > 2:
            overlay_config = configs[node_id][2]

            # overlay objects
            for obj in overlay_config.objects:
                for obj2 in card_config.objects:
                    if obj.name == obj2.name:
                        obj2.data_type = obj.data_type
                        break  # obj was found, search for next one

            # overlay tpdos
            for tpdo in overlay_config.tpdos:
                card_config.tpdos[tpdo].fields = overlay_config.tpdos[tpdo].fields
                card_config.tpdos[tpdo].delay_ms = overlay_config.tpdos[tpdo].delay_ms
                card_config.tpdos[tpdo].sync = overlay_config.tpdos[tpdo].sync

            # overlay rpdos
            for rpdo in overlay_config.rpdos:
                card_config.rpdos[rpdo].card = overlay_config.rpdos[rpdo].card
                card_config.rpdos[rpdo].tpdo_num = overlay_config.rpdos[rpdo].tpdo_num

        od = canopen.ObjectDictionary()
        od.bitrate = 1_000_000  # bps
        od.node_id = node_id.value
        od.device_information.allowed_baudrates = set([1000])
        od.device_information.vendor_name = "PSAS"
        od.device_information.vendor_number = 0
        od.device_information.product_name = NODE_NICE_NAMES[node_id]
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

        # add common and card records
        _add_rec(od, common_config.objects, Index.COMMON_DATA)
        _add_rec(od, card_config.objects, Index.CARD_DATA)

        # this object's subindexes are dependent on node id of all nodes on the bus
        # subindex corresponds to node_id (don't add subindexes for node id that do not exist)
        # all nodes other than the c3 really only need the c3
        #
        # without this firmware binary size for STM32M0-base cards becomes too large
        std_objects = set(card_config.std_objects + common_config.std_objects)
        if "consumer_heartbeat_time" in std_objects:
            obj = std_objs["consumer_heartbeat_time"]

            arr = canopen.objectdictionary.Array(obj.name, obj.index)
            od[obj.index] = arr

            var = canopen.objectdictionary.Variable("highest_index_supported", obj.index, 0x0)
            var.data_type = canopen.objectdictionary.UNSIGNED8
            var.access_type = "const"
            arr.add_member(var)

            if node_id != NodeId.C3:
                # add only the subindex for the c3 for non-c3 nodes
                arr.add_member(deepcopy(std_objs[obj.name][1]))
                var.default = 1
            else:
                # add all node_ids to c3
                for key in configs.keys():
                    if key == NodeId.C3:
                        continue  # skip itself
                    arr.add_member(deepcopy(std_objs[obj.name][key.value]))
                    var.default = key.value

        # add any standard objects
        for key in std_objects:
            if key == "consumer_heartbeat_time":
                continue  # added above, skip this
            od[std_objs[key].index] = deepcopy(std_objs[key])
            if key == "cob_id_emergency_message":
                od["cob_id_emergency_message"].default = 0x80 + node_id

        # add TPDSs
        _add_tpdo_data(od, card_config)
        if node_id != NodeId.C3:
            _add_tpdo_data(od, common_config)

        # set specific obj defaults
        od["common_data"]["satellite_id"].default = oresat_id.value
        if node_id == NodeId.C3:
            od["card_data"]["beacon_revision"].default = beacon_def["revision"]

        od_db[node_id] = od

    # add all RPDOs
    for node_id in configs:
        if node_id == NodeId.C3:
            continue
        _add_all_rpdo_data(od_db[NodeId.C3], od_db[node_id])
        _add_node_rpdo_data(configs[node_id][0], od_db[node_id], od_db)
        _add_node_rpdo_data(configs[node_id][1], od_db[node_id], od_db)

    # set all object values to its default value
    for od in od_db.values():
        for index in od:
            if not isinstance(od[index], canopen.objectdictionary.Variable):
                for subindex in od[index]:
                    od[index][subindex].value = od[index][subindex].default
            else:
                od[index].value = od[index].default

    return od_db
