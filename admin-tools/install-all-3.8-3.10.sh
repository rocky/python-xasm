#!/usr/bin/bash
PACKAGE_MODULE=python_control_flow
python_control_flow_owd=$(pwd)
bs=${BASH_SOURCE[0]}
mydir=$(dirname $bs)
python_control_flow_fulldir=$(readlink -f $mydir)
cd $python_control_flow_fulldir
. ./checkout_common.sh

pyenv_file="pyenv-3.8-3.10-versions"
if ! source $pyenv_file ; then
    echo "Having trouble reading ${pyenv_file} version $(pwd)"
    exit 1
fi

source ../${PACKAGE_MODULE}/version.py
if [[ ! $__version__ ]] ; then
    echo "Something is wrong: __version__ should have been set."
    exit 1
fi

cd ../dist/

install_file="python-control-flow_38-${__version__}.tar.gz"
install_check_command="python-cfg --version"
for version in $PYVERSIONS; do
    echo "*** Installing ${install_file} for Python ${version} ***"
    echo $version
    pyenv local $version
    pip install $install_file
    $install_check_command
    echo "----"
done
