"""Unit tests for validating the edl yaml config file."""

import re
import unittest

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
    # custom types
    "node_id",
    "opd_addr",
]


class ConfigTypes(unittest.TestCase):
    """Tests for the edl yaml config file."""

    def _test_snake_case(self, string: str):
        """Test that a string is snake_case."""

        regex_str = r"^[a-z][a-z0-9_]*[a-z0-9]*$"  # snake_case with no leading/trailing num or "_"
        self.assertIsNotNone(re.match(regex_str, string), f'"{string}" is not snake_case')

    def test_edl_commands(self):
        """Validate edl commands configs."""

        edl_commands = OreSatConfig(OreSatId.ORESAT0_5).edl_commands

        cmd_uids = [cmd.uid for cmd in edl_commands.values()]
        self.assertEqual(len(cmd_uids), len(set(cmd_uids)), "command uids are not unique")
        cmd_names = [cmd.name for cmd in edl_commands.values()]
        self.assertEqual(len(cmd_names), len(set(cmd_names)), "command names are not unique")

        for cmd in edl_commands.values():
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

            for req in cmd.request:
                self.assertIn(req.data_type, DATA_TYPES)
                self._test_snake_case(req.name)
                if req.name == "bytes":
                    self.assertTrue((req.fixed_size == 0) != (req.size_ref == ""))
                    if req.size_ref:
                        self.assertIn(
                            req.size_ref,
                            [req.name for req in cmd.request],
                            (
                                f"command {cmd.name} request field {req.name} is missing size "
                                "reference field {req.size_ref}"
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
            for res in cmd.response:
                self.assertIn(res.data_type, DATA_TYPES)
                self._test_snake_case(res.name)
                if res.name == "bytes":
                    self.assertTrue((res.fixed_size == 0) != (res.size_ref == ""))
                    if res.size_ref:
                        self.assertIn(
                            res.size_ref,
                            [res.name for res in cmd.response],
                            f"size_ref field {res.size_ref} is missing",
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
