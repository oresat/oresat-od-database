"""Utilities for top level cards definitions, not in the OD"""

import csv
import os
from dataclasses import dataclass

from dataclasses_json import dataclass_json

from .constants import Consts


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
        return {
            row["name"]: Card(
                row["nice_name"],
                int(row["node_id"], 16),
                row["processor"],
                int(row["opd_address"], 16),
                row["opd_always_on"].lower() == "true",
                row["child"],
            )
            for row in csv.DictReader(f)
            if row["name"] in oresat.cards_path
        }
