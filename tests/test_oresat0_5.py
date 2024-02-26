"""Unit tests for OreSat0.5 OD database."""

from oresat_configs import Consts, OreSatConfig

from . import TestConfig


class TestOreSat0_5(TestConfig):
    """Test the OreSat0.5 OD database"""

    def setUp(self):
        self.id = Consts.ORESAT0_5
        self.config = OreSatConfig(self.id)
