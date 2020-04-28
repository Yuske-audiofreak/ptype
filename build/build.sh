#!/bin/bash
set -u -o xtrace
# Build Python package.

# doesn't seem to work if I run in a virtualenv (can't find 'src' module)
# default to local Python 3.8 installation; use argument when building in GitHub runner.
pyexe=${1:-/usr/local/bin/python3.8}
$pyexe -m virtualenv venv
source venv/bin/activate

python -m pip install -r ../requirements.txt
pip freeze # useful for debugging

# build source distribution
python ../setup.py sdist || exit 1

# test
pushd ..
  # seems to be included by default, except in GitHub runner or virtualenv
  export PYTHONPATH=.

  # TODO: extract common helper script.
  python tests/test_ptype.py || exit 1
  if [[ $(git diff tests/column_type_counts.csv) ]]
  then
    echo "Test failed."
    exit 1
  else
    echo "Test passed."
  fi
  if [[ $(git diff tests/column_type_predictions.json) ]]
  then
    echo "Test failed."
    exit 1
  else
    echo "Test passed."
  fi
popd ... || exit
deactivate
rm -rf venv

set +o xtrace
echo Build completed successfully.

# python notebook_runner.py "../notebooks/demo.ipynb"
