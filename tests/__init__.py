"""Unit tests base for all OreSat OD databases."""

import unittest

import canopen
from oresat_od_db import Index, NodeId
from oresat_od_db._json_to_od import TPDO_PARA_START, OD_DATA_TYPE_SIZE


class TestConfig(unittest.TestCase):
    """Base class to test a OreSat OD databases."""

    def _test_tpdo_sizes(self, all_ods: dict):
        """Validate TPDO sizes."""

        for od in all_ods.values():
            for i in range(16):
                if TPDO_PARA_START + i not in od:
                    continue
                mapping_obj = od[TPDO_PARA_START + i]
                size = 0
                for sub in mapping_obj.subindices:
                    if sub == 0:
                        continue
                    raw = mapping_obj[sub].default
                    mapped_index = (raw & 0xFFFF0000) >> 16
                    mapped_subindex = (raw & 0x0000FF00) >> 8
                    mapped_obj = od[mapped_index]
                    if not isinstance(mapped_obj, canopen.objectdictionary.Variable):
                        mapped_obj = mapped_obj[mapped_subindex]
                    size += OD_DATA_TYPE_SIZE[mapped_obj.data_type]
                self.assertLessEqual(size, 64)

    def _test_beacon(self, all_ods: dict, beacon_def: dict):
        """Test all objects reference in the beacon definition exist in the C3's OD."""

        for i in beacon_def["fields"]:
            subindex = i[1]
            if i[0] == "c3":
                try:
                    obj = all_ods[NodeId.C3][Index.CARD_DATA][subindex]
                except KeyError:
                    obj = all_ods[NodeId.C3][Index.COMMON_DATA][subindex]
                self.assertIsNotNone(obj)
