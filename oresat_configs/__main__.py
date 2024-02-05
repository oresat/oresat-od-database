"""oresat_configs main"""

# Process for adding a new script:
# - Add module to scripts/ directory
#  - It must have register_subparser() which takes a subparsers list
# - import the module here and add it to the SCRIPTS list
# - If it can also be a standalone script then update the pyproject.toml [project.scripts] section
#
# test it out - both through oresat_configs and directly

import argparse

from .constants import __version__
from .scripts import gen_dcf
from .scripts import gen_fw_files
from .scripts import gen_xtce
from .scripts import print_od
from .scripts import sdo_transfer


SCRIPTS = [
    gen_dcf,
    gen_fw_files,
    gen_xtce,
    print_od,
    sdo_transfer,
]


def oresat_configs():
    """oresat_configs main."""
    parser = argparse.ArgumentParser(prog="oresat_configs")
    parser.add_argument('--version', action='version', version='%(prog)s v' + __version__)
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers(title="subcommands")

    for subcommand in SCRIPTS:
        subcommand.register_subparser(subparsers)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    oresat_configs()
