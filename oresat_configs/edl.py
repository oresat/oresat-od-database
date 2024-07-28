"""Used to parse edl.yaml that defines all EDL command requests and responses."""

import struct
from dataclasses import dataclass, field
from typing import Any, Union

from dacite import from_dict
from yaml import CLoader, load

_COMMAND_DATA_TYPES_SIZE = {
    "bool": 8,
    "int8": 8,
    "int16": 16,
    "int32": 32,
    "int64": 64,
    "uint8": 8,
    "uint16": 16,
    "uint32": 32,
    "uint64": 64,
    "float32": 32,
    "float64": 64,
}

_COMMAND_DATA_FMT = {
    "bool": "?",
    "int8": "b",
    "int16": "h",
    "int32": "i",
    "int64": "q",
    "uint8": "B",
    "uint16": "H",
    "uint32": "I",
    "uint64": "Q",
    "float32": "f",
    "float64": "d",
}


@dataclass
class EdlCommandField:
    """A field in EDL command request or response packet."""

    name: str
    """
    str: Unique name (scope of the fields in the command, not all fields in all commands) for the
    EDL command field.
    """
    data_type: str
    """
    str: Data type of field. Can be "intX", "uintX", "bool", "str", "bytes", or "bool" where X is
    a size in bits.
    """
    description: str = ""
    """str: A short description of the EDL command field."""
    enums: dict[str, int] = field(default_factory=dict)
    """dict[str, int]: Enum values for "intX", "uintX", or "bool" types."""
    max_size: int = 0
    """int: Max size in bytes for variable "str" data types. Takes precedence over fix_size."""
    fixed_size: int = 0
    """int: Fixed size in bytes for "bytes" or "str" data types."""
    size_ref: str = ""
    """str: Name of field to use to get the size in bytes for "bytes" data types."""
    unit: str = ""


@dataclass
class EdlCommand:
    """A EDL command."""

    uid: int
    """int: Unique id to identify the EDL command."""
    name: str
    """str: A unique snake_case name for the EDL command."""
    description: str = ""
    """str: A short description of the EDL command."""
    request: list[EdlCommandField] = field(default_factory=list)
    """list[EdlCommand]: List of request fields for the EDL command."""
    response: list[EdlCommandField] = field(default_factory=list)
    """list[EdlCommand]: List of response fields for the EDL command."""

    def _dynamic_len(self, fields: list[EdlCommandField]) -> bool:
        return True in [f.size_ref != "" for f in fields]

    def _decode(self, raw: bytes, fields: list[EdlCommandField]) -> tuple[Any]:

        if len(raw) == 0:
            raise ValueError("invalid packet size")

        # fixed size packet - quick decode
        if not self._dynamic_len(fields):
            fmt = "".join([_COMMAND_DATA_FMT[f.data_type] for f in fields])
            return struct.unpack(fmt, raw)

        # dynamic size packet - slower decode
        data: dict[str, Any] = {}
        offset = 0
        for f in fields:
            if f.data_type in _COMMAND_DATA_TYPES_SIZE:
                data_type_size = _COMMAND_DATA_TYPES_SIZE[f.data_type]
                tmp = raw[offset : offset + data_type_size]
                fmt = _COMMAND_DATA_FMT[f.data_type]
                data[f.name] = struct.unpack(fmt, tmp)
            elif f.size_ref != "":  # dynamic length
                data_type_size = data[f.size_ref]
                tmp = raw[offset : offset + data_type_size]
                if f.data_type == "bytes":
                    data[f.name] = tmp
                elif f.data_type == "str":
                    data[f.name] = tmp.decode()
            elif f.fixed_size != 0:  # fixed length
                data_type_size = f.fixed_size
                tmp = raw[offset : offset + data_type_size]
                if f.data_type == "bytes":
                    data[f.name] = tmp
                elif f.data_type == "str":
                    data[f.name] = tmp.decode()
            else:
                raise ValueError(f"invalid edl field {f.name}")
            offset += data_type_size

        return tuple(data.values())

    def _encode(self, values: tuple[Any], fields: list[EdlCommandField]) -> bytes:

        if len(values) != len(fields):
            raise ValueError("invalid number of values for packet")

        raw = self.uid.to_bytes(1, "little")

        # fixed size packet - quick encode
        if not self._dynamic_len(fields):
            fmt = "".join([_COMMAND_DATA_FMT[f.data_type] for f in fields])
            return raw + struct.pack(fmt, values)

        # dynamic size packet - slower encode
        data: dict[str, bytes] = {}
        for f, v in zip(fields, values):
            if f.data_type in _COMMAND_DATA_TYPES_SIZE:
                fmt = _COMMAND_DATA_FMT[f.data_type]
                data[f.name] = struct.pack(fmt, (v,))
            if f.data_type == "bytes":
                data[f.name] = v
            elif f.data_type == "str":
                data[f.name] = v.encode()
                if f.size_ref != "":  # dynamic length
                    index = -1
                    for i in fields:
                        if i.name == f.size_ref:
                            index = fields.index(f)
                            break
                    fmt = _COMMAND_DATA_FMT[fields[index].data_type]
                    data[f.size_ref] = struct.pack(fmt, len(v))
            else:
                raise ValueError(f"invalid edl field {f.name}")

        for f in fields:
            raw += data[f.name]
        return raw

    def decode_request(self, raw: bytes) -> tuple[Any]:
        """Decode a EDL request payload."""
        return self._decode(raw, self.request)

    def encode_request(self, values: tuple[Any]) -> bytes:
        """Encode a EDL request payload."""
        return self._encode(values, self.request)

    def decode_response(self, raw: bytes) -> tuple[Any]:
        """Decode a EDL response payload."""
        return self._decode(raw, self.response)

    def encode_response(self, values: tuple[Any]) -> bytes:
        """Encode a EDL reponse payload."""
        return self._encode(values, self.response)


class EdlCommands:
    """
    A custom dictionary-like class to store EDL commands that can use the EDL command uid and EDL
    command name as keys.
    """

    def __init__(self, file_path: str):
        self._names: dict[str, EdlCommand] = {}
        self._uids: dict[int, EdlCommand] = {}

        edl_commands_raw = {}
        with open(file_path, "r") as f:
            edl_commands_raw = load(f, Loader=CLoader)

        for command_raw in edl_commands_raw.get("commands", []):
            command = from_dict(data_class=EdlCommand, data=command_raw)
            self._uids[command.uid] = command
            self._names[command.name] = command

    def __getitem__(self, uid: Union[int, str]) -> EdlCommand:
        return self._uids.get(uid) or self._names.get(uid)  # type: ignore

    def __len__(self) -> int:
        return len(self._uids)

    def __iter__(self):
        return iter(self._uids)

    def values(self):
        """Get dictionary values."""
        return self._uids.values()
