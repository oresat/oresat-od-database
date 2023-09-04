"""Unit tests base for all OreSat OD databases."""

import unittest

import canopen
from oresat_od_db import Index, NodeId
from oresat_od_db._json_to_od import TPDO_PARA_START, OD_DATA_TYPE_SIZE


class TestConfig(unittest.TestCase):
    """Base class to test a OreSat OD databases."""

    def setUp(self):
        self.od_db = {NodeId.C3: canopen.ObjectDictionary()}
        self.beacon_def = {"fields": []}

    def test_tpdo_sizes(self):
        """Validate TPDO sizes."""

        for node in self.od_db:
            od = self.od_db[node]
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
                    self.assertTrue(
                        mapped_obj.pdo_mappable, f"{mapped_obj.name} is not pdo mappable"
                    )
                    size += OD_DATA_TYPE_SIZE[mapped_obj.data_type]
                self.assertLessEqual(size, 64, f"{node.name} TPDO{i + 1} is more than 64 bits")

    def test_beacon(self):
        """Test all objects reference in the beacon definition exist in the C3's OD."""

        length = 0

        dynamic_len_data_types = [
            canopen.objectdictionary.VISIBLE_STRING,
            canopen.objectdictionary.OCTET_STRING,
            canopen.objectdictionary.DOMAIN,
        ]

        c3_od = self.od_db[NodeId.C3]

        for i in self.beacon_def["fields"]:
            name = i[0]
            subindex = i[1]
            if name == "c3":
                # can be in either index for the c3
                try:
                    obj = c3_od[Index.CARD_DATA][subindex]
                except KeyError:
                    obj = c3_od[Index.COMMON_DATA][subindex]
            else:
                index = Index[f"{name.upper()}_DATA"].value
                obj = c3_od[index][subindex]
            self.assertNotIn(
                obj.data_type,
                dynamic_len_data_types,
                f"{name} {obj.name} is a dynamic length data type",
            )
            length += OD_DATA_TYPE_SIZE[obj.data_type] // 8  # bits to bytes

        # AX.25 payload max length = 255
        # Start chars = 3
        # CRC32 length = 4
        self.assertLessEqual(length, 255 - 3 - 4, "beacon length too long")
