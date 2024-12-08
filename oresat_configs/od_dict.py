"""Convert an canopen.ObjectDictionary into a dictionary and vice versa."""

from canopen import ObjectDictionary
from canopen.objectdictionary import OCTET_STRING, Array, Record, Variable

from ._yaml_to_od import DYNAMIC_LEN_DATA_TYPES

_VAR_ATTRS = [
    "index",
    "subindex",
    "name",
    "unit",
    "factor",
    "min",
    "max",
    "data_type",
    "description",
    "value_descriptions",
    "bit_definitions",
]


def var2dict(var: Variable) -> dict:
    """Convert an variable into a dictionary."""

    data = {"type": "variable"}

    if var.data_type == OCTET_STRING:
        data["default"] = var.default.hex()
    else:
        data["default"] = var.default

    return data | {name: getattr(var, name) for name in _VAR_ATTRS}


def od2dict(od: ObjectDictionary) -> dict:
    """Convert an object dictionary into a dictionary."""

    data = {
        "node_id": od.node_id,
        "product_name": od.device_information.product_name,
        "tpdos": od.device_information.nr_of_TXPDO,
        "rpdos": od.device_information.nr_of_RXPDO,
        "objects": [],
    }

    for obj in od.values():
        if isinstance(obj, Variable):
            obj_dict = var2dict(obj)
        elif isinstance(obj, Array):
            obj_dict = {
                "type": "array",
                "name": obj.name,
                "description": obj.description,
                "index": obj.index,
                "subindexes": [var2dict(obj[subindex]) for subindex in obj.subindices],
            }
        else:
            obj_dict = {
                "type": "record",
                "name": obj.name,
                "description": obj.description,
                "index": obj.index,
                "subindexes": [var2dict(obj[subindex]) for subindex in obj.subindices],
            }
        data["objects"].append(obj_dict)

    return data


def dict2var(data: dict) -> Variable:
    """Convert an dictionary into a variable."""

    var = Variable(data["name"], data["index"], data["subindex"])

    if var.data_type == OCTET_STRING:
        var.default = bytes.fromhex(data["default"])
    else:
        var.default = data["default"]
    var.value = var.default

    for name in _VAR_ATTRS:
        setattr(var, name, data[name])

    if var.data_type not in DYNAMIC_LEN_DATA_TYPES:
        var.pdo_mappable = True

    return var


def dict2od(data: dict) -> ObjectDictionary:
    """Convert an dictionary into a pbject dictionary."""

    od = ObjectDictionary()
    od.node_id = data["node_id"]
    od.device_information.product_name = data["product_name"]
    od.device_information.nr_of_TXPDO = data["tpdos"]
    od.device_information.nr_of_RXPDO = data["rpdos"]
    for obj in data["objects"]:
        if obj["type"] == "variable":
            od.add_object(dict2var(obj))
        elif obj["type"] == "array":
            arr = Array(obj["name"], obj["index"])
            arr.description = data["description"]
            for sub_obj in obj["subindexes"]:
                arr.add_member(dict2var(sub_obj))
            od.add_object(arr)
        else:
            rec = Record(obj["name"], obj["index"])
            rec.description = data["description"]
            for sub_obj in obj["subindexes"]:
                rec.add_member(dict2var(sub_obj))
            od.add_object(rec)

    return od
