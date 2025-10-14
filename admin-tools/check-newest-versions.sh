#!/bin/bash
function finish {
    if [[ -n ${xasm_owd} ]] && [[ -d $xasm_owd ]]; then
	cd $xasm_owd
    fi
}

# FIXME put some of the below in a common routine
xasm_owd=$(pwd)
# trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-newest-versions ; then
    exit $?
fi

if ! source ./setup-master.sh ; then
    exit $?
fi

cd ..
for version in $PYVERSIONS; do
    if ! pyenv local $version ; then
	exit $?
    fi
    python --version
    make clean && pip install -e .
    if ! make check; then
	exit $?
    fi
    echo === $version ===
done
