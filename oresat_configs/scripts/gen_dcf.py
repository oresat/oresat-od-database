"""Generate a DCF for from an OreSat card's object directory."""

import sys
from argparse import ArgumentParser
from datetime import datetime

import canopen

from .. import OreSatConfig, OreSatId

GEN_DCF = "generate DCF file for OreSat node(s)"
GEN_DCF_PROG = "oresat-gen-dcf"


def write_od(od: canopen.ObjectDictionary, dir_path: str = "."):
    """Save an od/dcf file

    Parameters
    ----------
    od: canopen.ObjectDictionary
        od data structure to save as file
    dir_path: str
        Directory path of dcf to save.
    """

    lines = []

    dev_info = od.device_information
    file_name = dev_info.product_name + ".dcf"
    file_name = file_name.lower().replace(" ", "_")
    file_path = f"{dir_path}/{file_name}"
    now = datetime.now()

    # file info seciton
    lines.append("[FileInfo]")
    lines.append(f"FileName={file_name}")
    lines.append("FileVersion=0")
    lines.append("FileRevision=0")
    lines.append("LastEDS=")
    lines.append("EDSVersion=4.0")
    lines.append("Description=")
    lines.append("CreationTime=" + now.strftime("%I:%M%p"))
    lines.append("CreationDate=" + now.strftime("%m-%d-%Y"))
    lines.append("CreatedBy=PSAS")
    lines.append("ModificationTime=" + now.strftime("%I:%M%p"))
    lines.append("ModificationDate=" + now.strftime("%m-%d-%Y"))
    lines.append("ModifiedBy=PSAS")
    lines.append("")

    # device info seciton
    lines.append("[DeviceInfo]")
    lines.append(f"VendorName={dev_info.vendor_name}")
    lines.append(f"VendorNumber={dev_info.vendor_number}")
    lines.append(f"ProductName={dev_info.product_name}")
    lines.append(f"ProductNumber={dev_info.product_number}")
    lines.append(f"RevisionNumber={dev_info.revision_number}")
    lines.append(f"OrderCode={dev_info.order_code}")
    for i in [10, 12, 50, 125, 250, 500, 800, 1000]:  # baud rates in kpps
        lines.append(f"BaudRate_{i}=1")
    lines.append(f"SimpleBootUpMaster={int(dev_info.simple_boot_up_master)}")
    lines.append(f"SimpleBootUpSlave={int(dev_info.simple_boot_up_slave)}")
    lines.append(f"Granularity={dev_info.granularity}")
    lines.append(f"DynamicChannelsSupported={int(dev_info.dynamic_channels_supported)}")
    lines.append(f"GroupMessaging={int(dev_info.group_messaging)}")
    lines.append(f"NrOfRXPDO={dev_info.nr_of_RXPDO}")
    lines.append(f"NrOfTXPDO={dev_info.nr_of_TXPDO}")
    lines.append(f"LSS_Supported={int(dev_info.LSS_supported)}")
    lines.append("")

    lines.append("[DeviceComissioning]")  # only one 'm' in header
    lines.append(f"NodeID=0x{od.node_id:X}")
    lines.append(f"NodeName={dev_info.product_name}")
    lines.append(f"BaudRate={od.bitrate // 1000}")  # in kpbs
    lines.append("NetNumber=0")
    lines.append("NetworkName=0")
    if dev_info.product_name in ["c3", "C3"]:
        lines.append("CANopenManager=1")
    else:
        lines.append("CANopenManager=0")
    lines.append("LSS_SerialNumber=0")
    lines.append("")

    lines.append("[DummyUsage]")
    for i in range(8):
        lines.append(f"Dummy000{i}=1")
    lines.append("")

    lines.append("[Comments]")
    lines.append("Lines=0")
    lines.append("")

    lines.append("[MandatoryObjects]")
    mandatory_objs = []
    for i in [0x1000, 0x1001, 0x1018]:
        if i in od:
            mandatory_objs.append(i)
    lines.append(f"SupportedObjects={len(mandatory_objs)}")
    for i in mandatory_objs:
        num = mandatory_objs.index(i) + 1
        value = f"0x{i:04X}"
        lines.append(f"{num}={value}")
    lines.append("")

    lines += _objects_lines(od, mandatory_objs)

    lines.append("[OptionalObjects]")
    optional_objs = []
    for i in od:
        if (i >= 0x1002 and i <= 0x1FFF and i != 0x1018) or (i >= 0x6000 and i <= 0xFFFF):
            optional_objs.append(i)
    lines.append(f"SupportedObjects={len(optional_objs)}")
    for i in optional_objs:
        num = optional_objs.index(i) + 1
        value = f"0x{i:04X}"
        lines.append(f"{num}={value}")
    lines.append("")

    lines += _objects_lines(od, optional_objs)

    lines.append("[ManufacturerObjects]")
    manufacturer_objs = []
    for i in od:
        if i >= 0x2000 and i <= 0x5FFF:
            manufacturer_objs.append(i)
    lines.append(f"SupportedObjects={len(manufacturer_objs)}")
    for i in manufacturer_objs:
        num = manufacturer_objs.index(i) + 1
        value = f"0x{i:04X}"
        lines.append(f"{num}={value}")
    lines.append("")

    lines += _objects_lines(od, manufacturer_objs)

    with open(file_path, "w") as f:
        for line in lines:
            f.write(line + "\n")


def _objects_lines(od: canopen.ObjectDictionary, indexes: list) -> list:
    lines = []

    for i in indexes:
        obj = od[i]
        if isinstance(obj, canopen.objectdictionary.Variable):
            lines += _variable_lines(obj, i)
        elif isinstance(obj, canopen.objectdictionary.Array):
            lines += _array_lines(obj, i)
        elif isinstance(obj, canopen.objectdictionary.Record):
            lines += _record_lines(obj, i)

    return lines


def _variable_lines(variable: canopen.objectdictionary.Variable, index: int, subindex=None) -> list:
    lines = []

    if subindex is None:
        lines.append(f"[{index:X}]")
    else:
        lines.append(f"[{index:X}sub{subindex:X}]")

    lines.append(f"ParameterName={variable.name}")
    lines.append("ObjectType=0x07")
    lines.append(f"DataType=0x{variable.data_type:04X}")
    lines.append(f"AccessType={variable.access_type}")
    if variable.default:  # optional
        if variable.data_type == canopen.objectdictionary.OCTET_STRING:
            tmp = variable.default.hex(sep=" ")
            lines.append(f"DefaultValue={tmp}")
        else:
            lines.append(f"DefaultValue={variable.default}")
    if variable.pdo_mappable:  # optional
        lines.append(f"PDOMapping={int(variable.pdo_mappable)}")
    lines.append("")

    return lines


def _array_lines(array: canopen.objectdictionary.Array, index: int) -> list:
    lines = []

    lines.append(f"[{index:X}]")

    lines.append(f"ParameterName={array.name}")
    lines.append("ObjectType=0x08")
    lines.append(f"SubNumber={len(array)}")
    lines.append("")

    for i in array.subindices:
        lines += _variable_lines(array[i], index, i)

    return lines


def _record_lines(record: canopen.objectdictionary.Record, index: int) -> list:
    lines = []

    lines.append(f"[{index:X}]")

    lines.append(f"ParameterName={record.name}")
    lines.append("ObjectType=0x09")
    lines.append(f"SubNumber={len(record)}")
    lines.append("")

    for i in record.subindices:
        lines += _variable_lines(record[i], index, i)

    return lines


def gen_dcf(sys_args=None):
    """Gen_dcf main."""

    if sys_args is None:
        sys_args = sys.argv[1:]

    parser = ArgumentParser(description=GEN_DCF, prog=GEN_DCF_PROG)
    parser.add_argument(
        "oresat", default="oresat0", help="oresat mission; oresat0, oresat0.5, or oresat1"
    )
    parser.add_argument("card", help="card name; all, c3, gps, star_tracker_1, etc")
    parser.add_argument("-d", "--dir-path", default=".", help='directory path; defautl "."')
    args = parser.parse_args(sys_args)

    arg_oresat = args.oresat.lower()
    if arg_oresat in ["0", "oresat0"]:
        oresat_id = OreSatId.ORESAT0
    elif arg_oresat in ["0.5", "oresat0.5"]:
        oresat_id = OreSatId.ORESAT0_5
    elif arg_oresat in ["1", "oresat1"]:
        oresat_id = OreSatId.ORESAT1
    else:
        print(f"invalid oresat mission: {args.oresat}")
        sys.exit()

    config = OreSatConfig(oresat_id)

    if args.card.lower() == "all":
        for od in config.od_db.values():
            write_od(od, args.dir_path)
    else:
        od = config.od_db[args.card.lower()]
        write_od(od, args.dir_path)
