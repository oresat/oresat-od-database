"""Unit tests for OreSat0 OD database."""

from oresat_configs import BEACON_DEF_DB, FRAM_DEF_DB, OD_DB, OreSatId

from . import TestConfig


class TestOreSat0(TestConfig):
    """Test the OreSat0 OD database."""

    def setUp(self):
        self.id = OreSatId.ORESAT0_5
        self.od_db = OD_DB[self.id]
        self.beacon_def = BEACON_DEF_DB[self.id]
        self.fram_def = FRAM_DEF_DB[self.id]
