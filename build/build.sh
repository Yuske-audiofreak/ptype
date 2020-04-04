#!/bin/bash
set -x
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

  python tests/test_ptype.py || exit 1
  # TODO: check agreement.
  if [[ $(git diff tests/column_type_counts.csv) ]]
  then
    echo "Unexpected test output."
  else
    echo "Expected test output."
    exit 1
  fi
  # show disparities, then discard; will check these later
  git diff tests/column_type_predictions.json
  git checkout tests/column_type_predictions.json
popd ... || exit
deactivate
rm -rf venv

# python notebook_runner.py "../notebooks/demo.ipynb"
