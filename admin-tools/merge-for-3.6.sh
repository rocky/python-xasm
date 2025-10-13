#/bin/bash
xasm_merge_36_owd=$(pwd)
PYTHON_VERSION=3.6
pyenv local $PYTHON_VERSION
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-3.8.sh; then
    git merge master
fi
cd $xasm_merge_36_owd
