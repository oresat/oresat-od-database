"""Used to parse edl_cmd_defs.yaml that defines all EDL command requests and responses."""

import struct
from dataclasses import dataclass, field
from typing import Any, Union

from dacite import from_dict
from yaml import CLoader, load

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
      - binary: `"bytes"` (NOTE: `fix_size` or `size_prefix` must be set.)
    """
    description: str = ""
    """str: A short description of the EDL command field."""
    enums: dict[str, int] = field(default_factory=dict)
    """dict[str, int]: Enum values for "uintX" or "bool" types."""
    max_size: int = 0
    """
    int: Max size in bytes for variable "str" data types. String must end with a '\0'.
    This takes precedence over fix_size.
    """
    size_prefix: int = 0
    """
    int: Number of leading prefix bytes used to determind the size of a "bytes" field.
    This takes precedence over fix_size.
    """
    fixed_size: int = 0
    """
    int: Fixed size in bytes for "bytes" or "str" data types. Value that are not the full size
    will be filled with "\0" at the end as padding.
    """
    unit: str = ""
    "str: Optional unit for the field"


@dataclass
class EdlCommandDefinition:
    """A EDL command."""

    uid: int
    """int: Unique id to identify the EDL command."""
    name: str
    """str: A unique snake_case name for the EDL command."""
    description: str = ""
    """str: A short description of the EDL command."""
    request: list[EdlCommandField] = field(default_factory=list)
    """list[EdlCommandDefinition]: List of request fields for the EDL command."""
    response: list[EdlCommandField] = field(default_factory=list)
    """list[EdlCommandDefinition]: List of response fields for the EDL command."""

    def _dynamic_len(self, fields: list[EdlCommandField]) -> bool:
        return True in [f.size_prefix != 0 for f in fields]

    def _decode(self, raw: bytes, fields: list[EdlCommandField]) -> tuple[Any]:

        # fixed size packet - quick decode
        if not self._dynamic_len(fields):
            fmt = "".join([_COMMAND_DATA_FMT[f.data_type] for f in fields])
            return struct.unpack(fmt, raw)

        # dynamic size packet - slower decode
        data: dict[str, Any] = {}
        offset = 0
        for f in fields:
            if f.data_type in _COMMAND_DATA_FMT:
                data_type_size = struct.calcsize(_COMMAND_DATA_FMT[f.data_type])
                tmp = raw[offset : offset + data_type_size]
                fmt = _COMMAND_DATA_FMT[f.data_type]
                data[f.name] = struct.unpack(fmt, tmp)[0]
            elif f.data_type == "bytes":
                if f.size_prefix != 0:  # dynamic length in bits
                    data_type_size_raw = raw[offset : offset + f.size_prefix]
                    data_type_size = int.from_bytes(data_type_size_raw, "little") // 8
                    offset += f.size_prefix
                else:  # fix_size
                    data_type_size = f.fixed_size
                data[f.name] = raw[offset : offset + data_type_size]
            elif f.data_type == "str":
                if f.max_size != "":  # dynamic length that ends with "\0"
                    data_type_size = raw[offset:].find(b"\0")
                else:  # fix_size
                    data_type_size = f.fixed_size
                data[f.name] = raw[offset : offset + data_type_size].decode()
            else:
                raise ValueError(f"invalid edl field {f.name}")
            offset += data_type_size

        return tuple(data.values())

    def _encode(self, values: tuple[Any], fields: list[EdlCommandField]) -> bytes:

        if not isinstance(values, (tuple, list)):
            values = (values,)

        if len(values) != len(fields):
            raise ValueError(
                f"invalid number of values for packet: got {len(values)} expected {len(fields)}"
            )

        # fixed size packet - quick encode
        if not self._dynamic_len(fields):
            fmt = "".join([_COMMAND_DATA_FMT[f.data_type] for f in fields])
            return struct.pack(fmt, *values)

        # dynamic size packet - slower encode
        raw = b""
        for f, v in zip(fields, values):
            if f.data_type in _COMMAND_DATA_FMT:
                fmt = _COMMAND_DATA_FMT[f.data_type]
                raw += struct.pack(fmt, v)
            elif f.data_type == "bytes":
                value = v
                if f.size_prefix != 0:  # dynamic length in bits
                    fmt = _COMMAND_DATA_FMT[f"uint{f.size_prefix * 8}"]
                    raw += struct.pack(fmt, len(v) * 8)
                else:  # fixed length
                    value += b"\x00" * (f.fixed_size - len(value))
                raw += value
            elif f.data_type == "str":
                value = v.encode()
                if f.max_size != "":  # dynamic length that ends with "\0"
                    value += b"\0"
                else:  # fixed length
                    value += b"\0" * (f.fixed_size - len(value))
                raw += value
            else:
                raise ValueError(f"invalid data type {f.data_type} for edl field {f.name}")
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


class EdlCommandDefinitions:
    """
    A custom dictionary-like class to store EDL commands that can use the EDL command uid and EDL
    command name as keys.
    """

    def __init__(self, file_path: str, custom_enums: dict[str, dict[str, int]] = {}):
        self._names: dict[str, EdlCommandDefinition] = {}
        self._uids: dict[int, EdlCommandDefinition] = {}

        _raw = {}
        with open(file_path, "r") as f:
            _raw = load(f, Loader=CLoader)

        for command_raw in _raw.get("commands", []):
            command = from_dict(data_class=EdlCommandDefinition, data=command_raw)
            command.description = command.description.replace("\n", "")
            for req in command.request:
                req.description = req.description.replace("\n", "")
                if req.name in custom_enums:
                    req.enums = custom_enums[req.name]
            for res in command.response:
                res.description = res.description.replace("\n", "")
                if res.name in custom_enums:
                    res.enums = custom_enums[res.name]
            self._uids[command.uid] = command
            self._names[command.name] = command

    def __getitem__(self, value: Union[int, str]) -> EdlCommandDefinition:
        return self._uids.get(value) or self._names.get(value)  # type: ignore

    def __len__(self) -> int:
        return len(self._uids)

    def __iter__(self):
        return iter(self._uids)

    def values(self):
        """Get dictionary values."""
        return self._uids.values()

    def names(self):
        """Get command names."""
        return self._names.keys()

    def uid(self):
        """Get command unique ids."""
        return self._uids.keys()
