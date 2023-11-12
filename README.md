# OreSat Configs

Firmware/software configurations for OreSat missions.

Includes:

- A centeralize "database" for all OreSat card object dictionaries (OD)
- Beacon definition for each OreSat mission
- The C3 F-RAM data definition (object values to be saved to the F-RAM chip)

Having all the OD defined in one place makes it much easier to update
OD definitions without having to go to each repo to update each cards OD.
Also, the C3 can easily import all the OD definitions to be used for SDO
transfers.

## How This Works

- All object dictionaries for a specific OreSat mission are defined by [YAML]
  files.
  - All the OD configs are in `oresat_configs/base/`
  - All the beacon configs (`beacon.yaml`)are in their mission directories: 
    `oresat_configs/oresat<mission_num>/`
- All card specific configs are are named `<card_name>.yaml` format.
  They contain all card specific objects and PDOs.
  - **NOTE:** The cards YAML are simular to CANopen's `.eds` files; they are
    for a device type, not a unique device on a CAN network (if you add an
    object to `solar.yaml`, all solar cards will have that object).
- The `sw_common.yaml` defines all CANopen standard objects, common objects,
  and common PDOs for all Octavo A8-based cards.
- The `fw_common.yaml` defines all CANopen standard objects, common objects,
  and common PDOs for all STM32-based cards.
- A `standard_object.yaml` contains some CANopen standard objects that any
  `<card_name>.yaml` or `*_common.yaml` can flag to include.
- The `beacon.yaml` file defines the beacon definition as all the data is
  pulled strait out the the C3's OD, which is mostly build from all other ODs.
- The `c3.yaml` file also defines what objects have their values periodically
  saved to the C3's F-RAM chip.

## Setup

Install project dev dependencies.

```bash
$ pip install -r requirements.txt
```

## Updating a Config

After updating configs for card(s), run the unit tests to validate all the
configs.

```bash
$ python3 -m unittest
```

If there are no errors, the configs are valid.

Build and install the new version of oresat-configs to build, test, and/or
import with.

Once the change have been tested with firmware/software, open a Pull
Request to this repo to get all changes into the next release.

## Build and Install Local Package

Just run the `build_and_install.sh` script.

```bash
$ ./build_and_install.sh
```

[YAML]: https://en.wikipedia.org/wiki/YAML
