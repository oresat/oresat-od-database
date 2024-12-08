"""OreSat OD database"""

# Checks that pyyaml is installed correctly. For performance reasons it must use the libyaml C
# bindings. To use them both libyaml must be installed on the local system, and pyyaml must have
# been built to use them. This works correctly on x86 systems, but on arm pyyaml is built by
# default to not include the bindings.
try:
    from yaml import CLoader
except ImportError as e:
    raise ImportError(
        "pyyaml missing/installed without libyaml bindings. See oresat-configs README.md for more"
    ) from e

import json
import os
import shutil
from importlib.resources import as_file
from typing import Union

from canopen import ObjectDictionary
from canopen.objectdictionary import Variable

from ._yaml_to_od import (
    _gen_c3_beacon_defs,
    _gen_c3_fram_defs,
    _gen_fw_base_od,
    _gen_od_db,
    _load_configs,
)
from .beacon_config import BeaconConfig
from .card_info import Card, cards_from_csv
from .constants import Mission, __version__
from .od_dict import dict2od, od2dict

__all__ = ["Card", "Mission", "__version__"]


class OreSatConfig:
    """All the configs for an OreSat mission."""

    CACHE_DIR_BASE = "/var/cache" if os.geteuid() == 0 else os.path.expanduser("~/.cache")
    CACHE_DIR_BASE += "/oresat_config"
    CACHE_DIR = f"{CACHE_DIR_BASE}/{__version__}"

    def __init__(self, mission: Union[Mission, str, None] = None, use_cache: bool = True):
        """The parameter mission may be:
        - a string, either short or long mission name ('0', 'OreSat0.5', ...)
        - a Mission (ORESAT0, ...)
        - Omitted or None, in which case Mission.default() is chosen

        It will be used to derive the appropriate Mission, the collection of
        constants associated with a specific oresat mission.
        """

        if mission is None:
            self.mission = Mission.default()
        elif isinstance(mission, str):
            self.mission = Mission.from_string(mission)
        elif isinstance(mission, Mission):
            self.mission = mission
        else:
            raise TypeError(f"Unsupported mission type: '{type(mission)}'")

        self.cache_dir = f"{self.CACHE_DIR}/{self.mission.filename()}"
        self.od_db: dict[str, ObjectDictionary] = {}
        self.beacon_def: list[list[Variable]] = []
        self.fram_def: list[list[Variable]] = []
        self.fw_base_od = _gen_fw_base_od(self.mission)

        gen_cache = True
        if use_cache:
            try:
                self._load_cache()
                gen_cache = False
            except Exception:  # pylint: disable=W0718
                pass

        with as_file(self.mission.cards) as path:
            self.cards = cards_from_csv(path)

        if gen_cache:
            with as_file(self.mission.beacon) as path:
                beacon_config = BeaconConfig.from_yaml(path)
            configs = _load_configs(self.cards, self.mission.overlays)
            self.od_db = _gen_od_db(self.mission, self.cards, beacon_config, configs)
            c3_od = self.od_db["c3"]
            self.beacon_def = _gen_c3_beacon_defs(c3_od, beacon_config)
            self.fram_def = _gen_c3_fram_defs(c3_od, configs["c3"])

        if use_cache and gen_cache:
            try:
                self._cache()
            except Exception:  # pylint: disable=W0718
                pass

    def _load_cache(self):
        for file_name in os.listdir(self.cache_dir):
            if file_name in ["beacon.json", "fram.json"]:
                continue
            name = file_name.split(".")[0]
            with open(f"{self.cache_dir}/{file_name}", "r") as f:
                self.od_db[name] = dict2od(json.load(f))
        c3_od = self.od_db["c3"]

        def _load_def(file_path: str, data: list[list[Variable]]):
            with open(file_path, "r") as f:
                for index, subindex in json.load(f):
                    if subindex == 0 and isinstance(c3_od[index], Variable):
                        data.append(c3_od[index])
                    else:
                        data.append(c3_od[index][subindex])

        _load_def(f"{self.cache_dir}/fram.json", self.fram_def)
        _load_def(f"{self.cache_dir}/beacon.json", self.beacon_def)

    def _cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        for name, od in self.od_db.items():
            with open(f"{self.cache_dir}/{name}.json", "w") as f:
                json.dump(od2dict(od), f, indent=2)
        with open(f"{self.cache_dir}/fram.json", "w") as f:
            json.dump([[obj.index, obj.subindex] for obj in self.fram_def], f, indent=2)
        with open(f"{self.cache_dir}/beacon.json", "w") as f:
            json.dump([[obj.index, obj.subindex] for obj in self.beacon_def], f, indent=2)

    @classmethod
    def clear_cache(cls):
        """Remove all version of oresat config from the cache."""
        shutil.rmtree(cls.CACHE_DIR_BASE)

    @classmethod
    def clean_cache(cls):
        """Remove all other version of oresat config from the cache."""
        for path in os.listdir(cls.CACHE_DIR_BASE):
            if not path.endswith(__version__):
                shutil.rmtree(f"{cls.CACHE_DIR_BASE}/{path}")


def cache_load_od(mission: Mission, card: str) -> ObjectDictionary:
    """Load an od froma the cache."""
    cache_dir = f"{OreSatConfig.CACHE_DIR}/{mission.filename()}"
    with open(f"{cache_dir}/{card}.json", "r") as f:
        return dict2od(json.load(f))
