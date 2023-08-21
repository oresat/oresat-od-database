import unittest

from oresat_configs.oresat0 import C3_OD, BEACON_DEF


class TestBeacon(unittest.TestCase):
    def test_beacon(self):
        for i in BEACON_DEF["fields"]:
            C3_OD[i[0]][i[1]]
