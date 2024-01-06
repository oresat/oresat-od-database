"""Unit tests for OreSat0 OD database."""

from oresat_configs import OreSatConfig, OreSatId

from . import TestConfig


class TestOreSat0(TestConfig):
    """Test the OreSat0 OD database."""

    def setUp(self):
        self.id = OreSatId.ORESAT0
        self.config = OreSatConfig(self.id)
