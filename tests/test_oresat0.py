"""Unit tests for OreSat0 OD database."""

from oresat_od_db.oresat0 import BEACON_DEF, OD_DB, ORESAT_ID

from . import TestConfig


class TestOreSat0(TestConfig):
    """Test the OreSat0 OD database."""

    def setUp(self):
        self.id = ORESAT_ID
        self.od_db = OD_DB
        self.beacon_def = BEACON_DEF
