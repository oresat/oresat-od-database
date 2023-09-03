"""Unitt tests for OreSat0.5 configs"""

import unittest

from oresat_configs import Index
from oresat_configs.oresat0 import C3_OD, BEACON_DEF


class TestBeacon(unittest.TestCase):
    """Test the beacon definition."""

    def test_beacon(self):
        """Test all objects reference in the beacon definition exist."""

        for i in BEACON_DEF["fields"]:
            index = Index[f"{i[0].upper()}_DATA"].value
            subindex = i[1]
            if i[0] == "c3":
                try:
                    index = Index.CARD_DATA
                    obj = C3_OD[index][subindex]
                except KeyError:
                    index = Index.CORE_DATA
                    obj = C3_OD[index][subindex]

                self.assertIsNotNone(obj)
