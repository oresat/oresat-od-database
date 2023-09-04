"""Unit tests for OreSat0.5 OD database."""

from oresat_od_db.oresat0_5 import OD_DB, BEACON_DEF

from . import TestConfig


class TestOreSat0_5(TestConfig):
    """Test the OreSat0.5 OD database"""

    def setUp(self):
        self.od_db = OD_DB
        self.beacon_def = BEACON_DEF
