# OreSat Object Dictionary Database

A centeralize "database" for all OreSat card object dictionaries (OD) and
beacon definition for each OreSat mission.

Having all the OD defined in one place makes it much easier to update
OD definitions without having to go to each repo to update each cards OD.
Also, the C3 can easily import all the OD definitions to be used for SDO
transfers.

## How This Works

- All object dictionaries for a specific OreSat mission are defined by YAMLs.
- A `standard_object.yaml` contains some CANopen standard objects that any
  `*_common.yaml` file can flag to include.
- The `sw_common.yaml` defines all CANopen standard objects, common objects,
  and common PDOs for all Octavo A8-based cards for a OreSat mission.
- The `fw_common.yaml` defines all CANopen standard objects, common objects,
  and common PDOs for all STM32-based cards for a OreSat mission.
- All card specific configs are are named `<card_name>.yaml` format.
  They contain all card specific objects and PDOs.
  - **NOTE:** The cards YAML are simular to CANopen's `.eds` files; they are for
    a device type, not a unique device on a CAN network.
- The `beacon.yaml` file defines the beacon definition as all the data is pulled
  strait out the the C3 OD, which is mostly build from all other ODs.
- All the configs are passed to `gen_od_db()` that reads in all configs
  cross reference so all OD definition of PDOs match.

## Updating a Config

After updating configs for card(s), run the unit tests to validate all the configs.

```bash
$ python3 -m unittest
```

If there are no errors, the configs are valid.

Build and install the new version of oresat-od-database to build/test/import with.

Once the change have been tested with firmware/software, open a Pull
Request to this repo to get all changes into the next release.

## Build and Install Local Package

Just run the build_and_install.sh script.

```bash
./build_and_install.sh
```
