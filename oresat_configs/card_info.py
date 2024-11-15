"""Utilities for top level cards definitions, not in the OD"""

import csv
from dataclasses import dataclass, fields

from .constants import Mission


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


def cards_from_csv(mission: Mission) -> dict[str, Card]:
    """Turns cards.csv into a dict of names->Cards, filtered by the current mission"""

    path = mission.paths.CARDS_CSV_PATH
    with path.open() as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames) if reader.fieldnames else set()
        expect = {f.name for f in fields(Card)}
        expect.add("name")  # the 'name' column is the keys of the returned dict; not in Card
        if cols - expect:
            raise TypeError(f"{path} has excess columns: {cols - expect}. Update class Card?")
        if expect - cols:
            raise TypeError(f"class Card expects more columns than {path} has: {expect - cols}")

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
        }
