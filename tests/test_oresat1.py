"""Unit tests for OreSat1 OD database."""

from oresat_configs import Consts, OreSatConfig

from . import TestConfig


class TestOreSat1(TestConfig):
    """Test the OreSat1 OD database"""

    def setUp(self):
        self.id = Consts.ORESAT1
        self.config = OreSatConfig(self.id)
