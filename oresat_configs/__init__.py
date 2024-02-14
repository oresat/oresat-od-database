"""OreSat OD database"""

from dataclasses import dataclass
from typing import Union

from ._yaml_to_od import (
    _gen_c3_beacon_defs,
    _gen_c3_fram_defs,
    _gen_fw_base_od,
    _gen_od_db,
    _load_configs,
)
from .base import FW_COMMON_CONFIG_PATH
from .beacon_config import BeaconConfig
from .card_info import Card, cards_from_csv
from .constants import Consts, NodeId, OreSatId, __version__

__all__ = ["Card", "Consts", "NodeId", "OreSatId", "__version__"]


class OreSatConfig:
    """All the configs for an OreSat mission."""

    def __init__(self, oresat: Union[OreSatId, Consts, str]):
        if isinstance(oresat, str):
            oresat = Consts.from_string(oresat)
        elif isinstance(oresat, OreSatId):
            oresat = Consts.from_id(oresat)
        elif not isinstance(oresat, Consts):
            raise TypeError(f"Unsupported oresat type: '{type(oresat)}'")

        self.oresat = oresat
        beacon_config = BeaconConfig.from_yaml(oresat.beacon_path)
        self.cards = cards_from_csv(oresat)
        self.configs = _load_configs(oresat.cards_path)
        self.od_db = _gen_od_db(oresat, self.cards, beacon_config, self.configs)
        c3_od = self.od_db["c3"]
        self.beacon_def = _gen_c3_beacon_defs(c3_od, beacon_config)
        self.fram_def = _gen_c3_fram_defs(c3_od, self.configs["c3"])
        self.fw_base_od = _gen_fw_base_od(oresat, FW_COMMON_CONFIG_PATH)
