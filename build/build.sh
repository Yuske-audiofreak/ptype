#!/bin/bash
# Build Python package. Make this more repeatable/platform-independent as time goes on.

# doesn't seem to work if I run in a virtualenv (can't find 'src' module)
pyexe=/usr/local/bin/python3.8

# build source distribution
$pyexe ../setup.py sdist || exit 1

# test
pushd ..
$pyexe tests/test_ptype.py || exit 1
popd ... || exit

# for now discard any result disparities; will check these later
git checkout test/column_type_counts.cvs
git checkout test/column_type_predictions.json

# python notebook_runner.py "../notebooks/demo.ipynb"
