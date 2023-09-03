"""Unit tests for OreSat0.5 configs."""

from oresat_configs.oresat0_5 import ALL_ODS, BEACON_DEF

from . import TestConfig


class TestOreSat0_5(TestConfig):
    """Test the OreSat0.5 configs."""

    def test_tpdo_sizes(self):
        """Validate OreSat0.5 TPDO sizes."""

        self._test_tpdo_sizes(ALL_ODS)

    def test_beacon(self):
        """Test all OreSat0.5 objects reference in the beacon definition exist."""

        self._test_beacon(ALL_ODS, BEACON_DEF)
