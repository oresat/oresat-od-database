#!/bin/bash -e
# Quick script to locally rebuild and reinstall the oresat-od-db package

python3 -m pip uninstall oresat-od-database -y
rm -rf dist/ *.egg-info/
python3 -m build
python3 -m pip install dist/*.whl
