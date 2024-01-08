"""Generage DBC Files"""

import os
from argparse import ArgumentParser
from .. import ORESAT_NICE_NAMES, OreSatConfig, OreSatId

GEN_DBC = "generate SavyCan database CAN file"
GEN_DBC_PROG = "oresat-gen-dbc"


def write_dbc(config: OreSatConfig, dir_path: str = '.') -> None:
    dir_path = os.path.abspath(dir_path)
    output_dbc_fn = f'{dir_path}/{config.oresat_id.name.lower()}.dbc'
    print(f'Writing DBC to {output_dbc_fn}')

    with open(output_dbc_fn, 'w+') as file:
        for card_name, od in config.od_db.items():
            print(f'Parsing {card_name}')


def gen_dbc(sys_args: any) -> None:
    """Gen_dbc main."""

    if sys_args is None:
        sys_args = sys.argv[1:]

    parser = ArgumentParser(description=GEN_DBC, prog=GEN_DBC_PROG)
    parser.add_argument(
        "oresat", choices=['oresat0', 'oresat0.5', 'oresat1'], help="oresat mission; oresat0, oresat0.5, or oresat1"
    )
    parser.add_argument("-d", "--dir-path", default=".", help='directory path; defautl "."')
    args = parser.parse_args(sys_args)

    oresat_id = {
        'oresat0': OreSatId.ORESAT0,
        'oresat0.5': OreSatId.ORESAT0_5,
        'oresat1': OreSatId.ORESAT1,
    }[args.oresat]

    config = OreSatConfig(oresat_id)
    write_dbc(config, args.dir_path)
