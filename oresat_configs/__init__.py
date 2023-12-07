"""OreSat OD database"""

import csv
import os
from dataclasses import dataclass

from dataclasses_json import dataclass_json

from ._yaml_to_od import _gen_c3_beacon_defs, _gen_c3_fram_defs, _gen_fw_base_od, _gen_od_db
from .base import FW_COMMON_CONFIG_PATH
from .beacon_config import BeaconConfig
from .constants import NODE_NICE_NAMES, ORESAT_NICE_NAMES, NodeId, OreSatId, __version__
from .oresat0 import ORESAT0_BEACON_CONFIG_PATH, ORESAT0_CARD_CONFIGS_PATH
from .oresat0_5 import ORESAT0_5_BEACON_CONFIG_PATH, ORESAT0_5_CARD_CONFIGS_PATH
from .oresat1 import ORESAT1_BEACON_CONFIG_PATH, ORESAT1_CARD_CONFIGS_PATH


@dataclass_json
@dataclass
class Card:
    """Card info."""

    nice_name: str
    """A nice name for the card."""
    node_id: int
    """CANopen node id."""
    processor: str
    """Processor type; e.g.: "octavo", "stm32", or "none"."""
    opd_address: int
    """OPD address."""
    opd_always_on: bool
    """Keep the card on all the time. Only for battery cards."""


class OreSatConfig:
    """All the configs for an OreSat mission."""

    CARD_CONFIGS = {
        OreSatId.ORESAT0: ORESAT0_CARD_CONFIGS_PATH,
        OreSatId.ORESAT0_5: ORESAT0_5_CARD_CONFIGS_PATH,
        OreSatId.ORESAT1: ORESAT1_CARD_CONFIGS_PATH,
    }

    BEACON_CONFIGS = {
        OreSatId.ORESAT0: ORESAT0_BEACON_CONFIG_PATH,
        OreSatId.ORESAT0_5: ORESAT0_5_BEACON_CONFIG_PATH,
        OreSatId.ORESAT1: ORESAT1_BEACON_CONFIG_PATH,
    }

    def __init__(self, oresat_id: OreSatId):
        self.oresat_id = oresat_id
        beacon_config_path = self.BEACON_CONFIGS[oresat_id]
        beacon_config = BeaconConfig.from_yaml(beacon_config_path)
        card_configs = self.CARD_CONFIGS[oresat_id]

        self.cards = {}
        file_path = f"{os.path.dirname(os.path.abspath(__file__))}/cards.csv"
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["name"]
                if name in card_configs:
                    del row["name"]
                    self.cards[name] = Card(
                        row["nice_name"],
                        int(row["node_id"], 16),
                        row["processor"],
                        int(row["opd_address"], 16),
                        row["opd_always_on"].lower() == "true",
                    )

        self.od_db = _gen_od_db(oresat_id, self.cards, beacon_config, card_configs)
        c3_od = self.od_db["c3"]
        self.beacon_def = _gen_c3_beacon_defs(c3_od, beacon_config)
        self.fram_def: list = []  # _gen_c3_fram_defs(c3_od, c3_config)
        self.fw_base_od = _gen_fw_base_od(oresat_id, FW_COMMON_CONFIG_PATH)
