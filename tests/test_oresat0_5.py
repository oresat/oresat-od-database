"""Unit tests for OreSat0.5 OD database."""

from oresat_configs import OreSatConfig, OreSatId

from . import TestConfig


class TestOreSat0_5(TestConfig):
    """Test the OreSat0.5 OD database"""

    def setUp(self):
        self.id = OreSatId.ORESAT0_5
        self.config = OreSatConfig(self.id)
