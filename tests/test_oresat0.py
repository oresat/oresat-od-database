"""Unit tests for OreSat0 OD database."""

from oresat_od_db.oresat0 import ORESAT_ID, OD_DB, BEACON_DEF

from . import TestConfig


class TestOreSat0(TestConfig):
    """Test the OreSat0 OD database."""

    def setUp(self):
        self.id = ORESAT_ID
        self.od_db = OD_DB
        self.beacon_def = BEACON_DEF
