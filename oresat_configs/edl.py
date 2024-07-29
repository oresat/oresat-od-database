"""Used to parse edl.yaml that defines all EDL command requests and responses."""

import struct
from dataclasses import dataclass, field
from typing import Any, Union

from dacite import from_dict
from yaml import CLoader, load

_COMMAND_DATA_TYPES_SIZE = {
    "bool": 1,
    "int8": 1,
    "int16": 2,
    "int32": 4,
    "int64": 8,
    "uint8": 1,
    "uint16": 2,
    "uint32": 4,
    "uint64": 8,
    "float32": 4,
    "float64": 8,
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
    str: Data type of field.

    Can be:
      - signed integers: `"int8"`, `"int16"`, `"int32"`, `"int64"`
      - unsigned integers: `"uint8"`, `"uint16"`, `"uint32"`, `"uint64"`
      - floats: `"float32"`, `"float64"`
      - string: `"str"` (NOTE: `fix_size` or `max_size` must be set.)
      - binary: `"bytes"` (NOTE: `fix_size` or `size_ref` must be set.)
    """
    description: str = ""
    """str: A short description of the EDL command field."""
    enums: dict[str, int] = field(default_factory=dict)
    """dict[str, int]: Enum values for "uintX" or "bool" types."""
    max_size: int = 0
    """
    int: Max size in bytes for variable "str" data types. String must end with a '\0'.
    Takes precedence over fix_size.
    """
    fixed_size: int = 0
    """
    int: Fixed size in bytes for "bytes" or "str" data types. Value that are not the full size will
    be filled with "\0" at the end as padding.
    """
    size_ref: str = ""
    """str: Name of field to use to get the size in bytes for "bytes" data types."""
    unit: str = ""
    "str: Optional unit for the field"


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

    def _get_field(self, name: str, fields: list[EdlCommandField]) -> EdlCommandField:

        for req in fields:
            if req.name == name:
                return req
        raise ValueError(f"no field named {name}")

    def get_request_field(self, name: str) -> EdlCommandField:
        """Get a request field based of a name."""
        return self._get_field(name, self.request)

    def get_response_field(self, name: str) -> EdlCommandField:
        """Get a respone field based of a name."""
        return self._get_field(name, self.response)

    def _dynamic_len(self, fields: list[EdlCommandField]) -> bool:
        return True in [f.size_ref != "" for f in fields]

    def _decode(self, raw: bytes, fields: list[EdlCommandField]) -> tuple[Any]:

        if len(raw) == 0:
            raise ValueError("packet size must be greater than 0")

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
                data[f.name] = struct.unpack(fmt, tmp)[0]
            elif f.data_type == "bytes":
                if f.size_ref != "":  # dynamic length
                    data_type_size = data[f.size_ref]
                else:  # fix_size
                    data_type_size = f.fixed_size
                data[f.name] = raw[offset : offset + data_type_size]
            elif f.data_type == "str":
                if f.max_size != "":  # dynamic length
                    data_type_size = raw[offset:].find(b"\0")
                else:  # fix_size
                    data_type_size = f.fixed_size
                data[f.name] = raw[offset : offset + data_type_size].decode()
            else:
                raise ValueError(f"invalid edl field {f.name}")
            offset += data_type_size

        return tuple(data.values())

    def _encode(self, values: tuple[Any], fields: list[EdlCommandField]) -> bytes:

        if len(values) != len(fields):
            raise ValueError(
                f"invalid number of values for packet: got {len(fields)} expected {len(values)}"
            )

        # fixed size packet - quick encode
        if not self._dynamic_len(fields):
            fmt = "".join([_COMMAND_DATA_FMT[f.data_type] for f in fields])
            return struct.pack(fmt, *values)

        # dynamic size packet - slower encode
        data: dict[str, bytes] = {}
        for f, v in zip(fields, values):
            if f.data_type in _COMMAND_DATA_TYPES_SIZE:
                fmt = _COMMAND_DATA_FMT[f.data_type]
                data[f.name] = struct.pack(fmt, v)
            elif f.data_type == "bytes":
                value = v
                if f.size_ref != "":  # dynamic length
                    index = [i.name for i in fields].index(f.size_ref)
                    fmt = _COMMAND_DATA_FMT[fields[index].data_type]
                    data[f.size_ref] = struct.pack(fmt, len(v))
                else:  # fixed length
                    value += b"\x00" * (f.fixed_size - len(value))
                data[f.name] = value
            elif f.data_type == "str":
                value = v.encode()
                if f.max_size != 0:  # dynamic length
                    value += b"\0"
                else:  # fixed length
                    value += b"\0" * (f.fixed_size - len(value))
                data[f.name] = value
            else:
                raise ValueError(f"invalid data type {f.data_type} for edl field {f.name}")

        raw = b""
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

    def __init__(self, file_path: str, custom_enums: dict[str, dict[str, int]] = {}):
        self._names: dict[str, EdlCommand] = {}
        self._uids: dict[int, EdlCommand] = {}

        edl_commands_raw = {}
        with open(file_path, "r") as f:
            edl_commands_raw = load(f, Loader=CLoader)

        for command_raw in edl_commands_raw.get("commands", []):
            command = from_dict(data_class=EdlCommand, data=command_raw)
            for req in command.request:
                if req.name in custom_enums:
                    req.enums = custom_enums[req.name]
            for res in command.response:
                if res.name in custom_enums:
                    res.enums = custom_enums[res.name]
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
