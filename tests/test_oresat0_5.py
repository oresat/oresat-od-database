import unittest

from oresat_configs import Index
from oresat_configs.oresat0 import C3_OD, BEACON_DEF


class TestBeacon(unittest.TestCase):
    def test_beacon(self):
        for i in BEACON_DEF["fields"]:
            index = Index[f"{i[0].upper()}_DATA"].value
            if i[0] == "c3":
                index = Index.CARD_DATA
            subindex = i[1]
            C3_OD[index][subindex]
