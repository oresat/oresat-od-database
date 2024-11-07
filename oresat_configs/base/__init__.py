"""OreSat od base configs."""

from importlib import abc, resources
from typing import Optional

ConfigPaths = dict[str, Optional[tuple[abc.Traversable, ...]]]

_CONFIGS_DIR = resources.files(__name__)
FW_COMMON_CONFIG_PATH = _CONFIGS_DIR / "fw_common.yaml"
SW_COMMON_CONFIG_PATH = _CONFIGS_DIR / "sw_common.yaml"
C3_CONFIG_PATH = _CONFIGS_DIR / "c3.yaml"
BAT_CONFIG_PATH = _CONFIGS_DIR / "battery.yaml"
SOLAR_CONFIG_PATH = _CONFIGS_DIR / "solar.yaml"
ADCS_CONFIG_PATH = _CONFIGS_DIR / "adcs.yaml"
RW_CONFIG_PATH = _CONFIGS_DIR / "reaction_wheel.yaml"
GPS_CONFIG_PATH = _CONFIGS_DIR / "gps.yaml"
ST_CONFIG_PATH = _CONFIGS_DIR / "star_tracker.yaml"
DXWIFI_CONFIG_PATH = _CONFIGS_DIR / "dxwifi.yaml"
CFC_CONFIG_PATH = _CONFIGS_DIR / "cfc.yaml"
DIODE_CONFIG_PATH = _CONFIGS_DIR / "diode_test.yaml"
