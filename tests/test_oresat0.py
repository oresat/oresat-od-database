"""Unit tests for OreSat0 OD database."""

from oresat_configs import OreSatConfig, Consts

from . import TestConfig


class TestOreSat0(TestConfig):
    """Test the OreSat0 OD database."""

    def setUp(self):
        self.id = Consts.ORESAT0
        self.config = OreSatConfig(self.id)
