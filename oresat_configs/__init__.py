"""OreSat OD database"""

import csv
import os
from dataclasses import dataclass, fields
from typing import Union

from dataclasses_json import dataclass_json

from ._yaml_to_od import (
    _gen_c3_beacon_defs,
    _gen_c3_fram_defs,
    _gen_fw_base_od,
    _gen_od_db,
    _load_configs,
)
from .base import FW_COMMON_CONFIG_PATH
from .beacon_config import BeaconConfig
from .constants import Consts, NodeId, OreSatId, __version__


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
    child: str = ""
    """Optional child node name. Useful for CFC cards."""


def cards_from_csv(oresat: Consts) -> dict[str, Card]:
    """Turns cards.csv into a dict of names->Cards, filtered by the current mission"""

    file_path = f"{os.path.dirname(os.path.abspath(__file__))}/cards.csv"
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames) if reader.fieldnames else set()
        expect = {f.name for f in fields(Card)}
        expect.add("name")  # the 'name' column is the keys of the returned dict; not in Card
        if cols - expect:
            raise TypeError(f"cards.csv has excess columns: {cols-expect}. Update class Card?")
        if expect - cols:
            raise TypeError(f"class Card expects more columns than cards.csv has: {expect-cols}")

        return {
            row["name"]: Card(
                row["nice_name"],
                int(row["node_id"], 16),
                row["processor"],
                int(row["opd_address"], 16),
                row["opd_always_on"].lower() == "true",
                row["child"],
            )
            for row in reader
            if row["name"] in oresat.cards_path
        }


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
