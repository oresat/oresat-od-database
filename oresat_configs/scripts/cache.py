"""Generate a DBC file for SavvyCAN."""

import os
from argparse import ArgumentParser, Namespace
from typing import Optional

from .. import Mission, OreSatConfig

CACHE = "control the oresat configs cache"


def build_parser(parser: ArgumentParser) -> ArgumentParser:
    """Configures an ArgumentParser suitable for this script.

    The given parser may be standalone or it may be used as a subcommand in another ArgumentParser.
    """
    parser.description = CACHE
    parser.add_argument("command", choices=["generate", "clean", "clear", "list"])
    parser.add_argument(
        "--oresat",
        default="all",
        choices=[m.arg for m in Mission] + ["all"],
        help="Oresat Mission. (Default: %(default)s)",
    )
    return parser


def register_subparser(subparsers):
    """Registers an ArgumentParser as a subcommand of another parser.

    Intended to be called by __main__.py for each script. Given the output of add_subparsers(),
    (which I think is a subparser group, but is technically unspecified) this function should
    create its own ArgumentParser via add_parser(). It must also set_default() the func argument
    to designate the entry point into this script.
    See https://docs.python.org/3/library/argparse.html#sub-commands, especially the end of that
    section, for more.
    """
    parser = build_parser(subparsers.add_parser("cache", help=CACHE))
    parser.set_defaults(func=cache)


def cache(args: Optional[Namespace] = None):
    """Cache main."""
    if args is None:
        args = build_parser(ArgumentParser()).parse_args()

    if args.command == "clear":
        OreSatConfig.clear_cache()
    elif args.command == "clean":
        OreSatConfig.clean_cache()
    elif args.command == "generate":
        if args.oresat == "all":
            for m in Mission:
                OreSatConfig(m, True)
        else:
            OreSatConfig(args.oresat, True)
    elif args.command == "list":
        print(OreSatConfig.CACHE_DIR_BASE)
        if not os.path.exists(OreSatConfig.CACHE_DIR_BASE):
            return
        for version_dir in os.listdir(OreSatConfig.CACHE_DIR_BASE):
            print(f"{' ' * 4}{version_dir}")
            version_path = f"{OreSatConfig.CACHE_DIR_BASE}/{version_dir}"
            for mission_dir in os.listdir(version_path):
                print(f"{' ' * 8}{mission_dir}")
