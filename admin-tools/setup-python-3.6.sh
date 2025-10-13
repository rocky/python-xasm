#!/bin/bash
PYTHON_VERSION=3.6

xasm_owd=$(pwd)
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

mydir=$(dirname $bs)
xasm_fulldir=$(readlink -f $mydir)
. $mydir/checkout_common.sh

(cd $xasm_fulldir/../.. && setup_version python-xdis python-3.6)
checkout_finish python-3.6-to-3.10
