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
from .scripts import gen_dcf, gen_fw_files, gen_xtce, list_cards, pdo, print_od, sdo_transfer

# TODO: Group by three categories in help:
#   - info (card, od)
#   - action (sdo, pdo)
#   - generate (dcf, xtce, fw)
# There can only be one subparsers group though, the other groupings
# would have to be done through add_argument_group() but those can't
# make subparser groups.

SCRIPTS = [
    list_cards,
    print_od,
    sdo_transfer,
    pdo,
    gen_dcf,
    gen_xtce,
    gen_fw_files,
]


def oresat_configs() -> None:
    """oresat_configs main."""
    parser = argparse.ArgumentParser(prog="oresat_configs")
    parser.add_argument("--version", action="version", version="%(prog)s v" + __version__)
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers(title="subcommands")

    for subcommand in SCRIPTS:
        subcommand.register_subparser(subparsers)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    oresat_configs()
