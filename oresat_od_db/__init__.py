"""OreSat OD database"""

from .constants import NODE_NICE_NAMES, Index, NodeId, OreSatId, __version__
from .oresat0 import ORESAT0_BEACON_DEF, ORESAT0_OD_DB
from .oresat0_5 import ORESAT0_5_BEACON_DEF, ORESAT0_5_OD_DB

OD_DB = {
    OreSatId.ORESAT0: ORESAT0_OD_DB,
    OreSatId.ORESAT0_5: ORESAT0_5_OD_DB,
}

BEACON_DEF_DB = {
    OreSatId.ORESAT0: ORESAT0_BEACON_DEF,
    OreSatId.ORESAT0_5: ORESAT0_5_BEACON_DEF,
}
