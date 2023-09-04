"""Unit tests for OreSat0 OD database."""

from oresat_od_db.oresat0 import OD_DB, BEACON_DEF

from . import TestConfig


class TestOreSat0(TestConfig):
    """Test the OreSat0 OD database."""

    def setUp(self):
        self.od_db = OD_DB
        self.beacon_def = BEACON_DEF
