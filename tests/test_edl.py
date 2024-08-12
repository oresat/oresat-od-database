"""Unit tests for validating the edl yaml config file."""

import re
import unittest
from random import choice, randbytes, randint, uniform
from string import ascii_letters
from typing import Any

from oresat_configs import OreSatConfig, OreSatId

DATA_TYPES = [
    "bool",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float32",
    "float64",
    "str",
    "bytes",
]


def _gen_random_value(data_type: str, length: int = 0) -> Any:
    """Generate a random value for non-custom data types."""

    value: Any = None
    if data_type == "bool":
        value = bool(randint(0, 1))
    elif data_type.startswith("int"):
        bits = int(data_type[3:])
        value = randint(-(2 ** (bits - 1)), 2 ** (bits - 1) - 1)
    elif data_type.startswith("uint"):
        bits = int(data_type[4:])
        value = randint(0, 2**bits - 1)
    elif data_type.startswith("float"):
        value = uniform(-1_000.0, 1_000.0)
    elif data_type == "str":
        value = "".join(choice(ascii_letters) for i in range(length))
    elif data_type == "bytes":
        value = randbytes(length)
    else:
        raise ValueError(f"invalid data type {data_type}")

    return value


class ConfigTypes(unittest.TestCase):
    """Tests for the edl yaml config file."""

    def _test_snake_case(self, string: str):
        """Test that a string is snake_case."""

        regex_str = r"^[a-z][a-z0-9_]*[a-z0-9]*$"  # snake_case with no leading/trailing num or "_"
        self.assertIsNotNone(re.match(regex_str, string), f'"{string}" is not snake_case')

    def test_edl_cmd_defs(self):
        """Validate edl commands configs."""

        edl_cmd_defs = OreSatConfig(OreSatId.ORESAT0_5).edl_cmd_defs

        cmd_uids = [cmd.uid for cmd in edl_cmd_defs.values()]
        self.assertEqual(len(cmd_uids), len(set(cmd_uids)), "command uids are not unique")
        cmd_names = [cmd.name for cmd in edl_cmd_defs.values()]
        self.assertEqual(len(cmd_names), len(set(cmd_names)), "command names are not unique")

        for cmd in edl_cmd_defs.values():
            req_names = [req.name for req in cmd.request]
            self.assertEqual(
                len(req_names),
                len(set(req_names)),
                f"command {cmd.name} request fields names are not unique",
            )
            res_names = [res.name for res in cmd.response]
            self.assertEqual(
                len(res_names),
                len(set(res_names)),
                f"command {cmd.name} response fields names are not unique",
            )

            test_values = tuple()
            for req in cmd.request:
                self.assertIn(req.data_type, DATA_TYPES)
                self._test_snake_case(req.name)
                if req.name == "bytes":
                    self.assertTrue(
                        (req.fixed_size == 0) != (req.size_prefix == 0),
                        (
                            f"command {cmd.name} request field {req.name} has both fixed_size "
                            "and size_prefix set"
                        ),
                    )
                    self.assertIn(
                        req.size_prefix,
                        [0, 1, 2, 4, 8],
                        (
                            f"command {cmd.name} request field {req.name} size_prefix "
                            "size not a standard integer size or 0"
                        ),
                    )
                elif req.name == "str":
                    self.assertFalse(
                        (req.fixed_size == 0) and (req.max_size == 0),
                        (
                            f"command {cmd.name} request field {req.name} has nether fixed_size and"
                            " max_size set",
                        ),
                    )
                    self.assertTrue(
                        (req.fixed_size == 0) != (req.max_size == 0),
                        (
                            f"command {cmd.name} request field {req.name} has both fixed_size and "
                            "max_size set",
                        ),
                    )
                size = 0
                if req.data_type == "bytes":
                    size = req.fixed_size
                    if req.size_prefix > 0:
                        size = randint(1, 100)  # set the random size to be reasonable
                elif req.data_type == "str":
                    size = req.fixed_size
                    if req.max_size != 0:
                        size = req.max_size
                test_values += (_gen_random_value(req.data_type, size),)
            if len(test_values) > 0:
                raw = cmd.encode_request(test_values)
                test_values2 = cmd.decode_request(raw)
                self.assertTupleEqual(
                    test_values,
                    test_values2,
                    f"command {cmd.name} request encode -> decode does not match",
                )

            test_values = tuple()
            for res in cmd.response:
                self.assertIn(res.data_type, DATA_TYPES)
                self._test_snake_case(res.name)
                if res.name == "bytes":
                    self.assertTrue(
                        (res.fixed_size == 0) != (res.size_prefix == 0),
                        (
                            f"command {cmd.name} request field {res.name} has both fixed_size "
                            "and size_prefix set"
                        ),
                    )
                    self.assertIn(
                        res.size_prefix,
                        [0, 1, 2, 4, 8],
                        (
                            f"command {cmd.name} request field {res.name} size_prefix "
                            "size not a standard integer size or 0"
                        ),
                    )
                elif res.name == "str":
                    self.assertFalse(
                        (res.fixed_size == 0) and (res.max_size == 0),
                        (
                            f"command {cmd.name} response field {res.name} has nether fixed_size "
                            "and max_size set",
                        ),
                    )
                    self.assertTrue(
                        (res.fixed_size == 0) != (res.max_size == 0),
                        (
                            f"command {cmd.name} response field {res.name} has both fixed_size and "
                            "max_size set",
                        ),
                    )
                size = 0
                if res.data_type == "bytes":
                    size = res.fixed_size
                    if res.size_prefix > 0:
                        size = randint(1, 100)  # set the random size to be reasonable
                elif res.data_type == "str":
                    size = res.fixed_size
                    if res.max_size != 0:
                        size = res.max_size
                test_values += (_gen_random_value(res.data_type, size),)
            if len(test_values) > 0:
                raw = cmd.encode_response(test_values)
                test_values2 = cmd.decode_response(raw)
                self.assertTupleEqual(
                    test_values,
                    test_values2,
                    f"command {cmd.name} response encode -> decode does not match",
                )
