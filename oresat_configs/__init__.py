"""OreSat OD database"""

import yaml
import canopen

from .constants import NODE_NICE_NAMES, ORESAT_NICE_NAMES, NodeId, OreSatId, __version__
from .oresat0 import ORESAT0_CARD_CONFIGS, ORESAT0_BEACON_CONFIG
from .oresat0_5 import ORESAT0_5_CARD_CONFIGS, ORESAT0_5_BEACON_CONFIG
from .oresat1 import ORESAT1_CARD_CONFIGS, ORESAT1_BEACON_CONFIG
from ._yaml_to_od import _gen_od_db, _gen_c3_fram_defs, _gen_c3_beacon_defs, _gen_fw_base_od
from .base import FW_COMMON_CONFIG, C3_CONFIG


class OreSatConfig:
    """All the configs for an OreSat mission."""

    CARD_CONFIGS = {
        OreSatId.ORESAT0: ORESAT0_CARD_CONFIGS,
        OreSatId.ORESAT0_5: ORESAT0_5_CARD_CONFIGS,
        OreSatId.ORESAT1: ORESAT1_CARD_CONFIGS,
    }

    BEACON_CONFIGS = {
        OreSatId.ORESAT0: ORESAT0_BEACON_CONFIG,
        OreSatId.ORESAT0_5: ORESAT0_5_BEACON_CONFIG,
        OreSatId.ORESAT1: ORESAT1_BEACON_CONFIG,
    }

    def __init__(self, oresat_id: OreSatId):

        self.oresat_id = oresat_id
        beacon_config = self.BEACON_CONFIGS[oresat_id]
        self.od_db = _gen_od_db(oresat_id, beacon_config, self.CARD_CONFIGS[oresat_id])
        c3_od = self.od_db[NodeId.C3]
        self.beacon_def = _gen_c3_beacon_defs(c3_od, beacon_config)
        self.fram_def = _gen_c3_fram_defs(c3_od, C3_CONFIG)
        self.fw_base_od = _gen_fw_base_od(oresat_id, FW_COMMON_CONFIG)
