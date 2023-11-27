"""oresat_configs main"""

import sys

from .constants import __version__
from .scripts.gen_dcf import GEN_DCF, GEN_DCF_PROG, gen_dcf
from .scripts.gen_fw_files import GEN_FW_FILES, GEN_FW_FILES_PROG, gen_fw_files
from .scripts.gen_xtce import GEN_XTCE, GEN_XTCE_PROG, gen_xtce
from .scripts.print_od import PRINT_OD, PRINT_OD_PROG, print_od
from .scripts.sdo_transfer import SDO_TRANSFER, SDO_TRANSFER_PROG, sdo_transfer

SCRIPTS = {
    GEN_DCF_PROG: GEN_DCF,
    GEN_XTCE_PROG: GEN_XTCE,
    GEN_FW_FILES_PROG: GEN_FW_FILES,
    PRINT_OD_PROG: PRINT_OD,
    SDO_TRANSFER_PROG: SDO_TRANSFER,
}


def oresat_configs():
    """oresat_configs main."""

    print("oresat_configs v" + __version__)
    print("")

    print("command : description")
    print("--------------------------")
    for key in SCRIPTS:
        print(f"{key} : {SCRIPTS[key]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        oresat_configs()
    elif sys.argv[1] == GEN_DCF_PROG:
        gen_dcf(sys.argv[2:])
    elif sys.argv[1] == GEN_FW_FILES_PROG:
        gen_fw_files(sys.argv[2:])
    elif sys.argv[1] == PRINT_OD_PROG:
        print_od(sys.argv[2:])
    elif sys.argv[1] == SDO_TRANSFER_PROG:
        sdo_transfer(sys.argv[2:])
    elif sys.argv[1] == GEN_XTCE_PROG:
        gen_xtce(sys.argv[2:])
    else:
        oresat_configs()
