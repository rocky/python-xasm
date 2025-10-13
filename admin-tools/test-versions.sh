#!/bin/bash
# Run "make check" over lots of python versions
test_version_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
cd ..
for v in 3.8 3.9 3.10 3.11 3.12 ; do
    echo ==== $v =====;
    pyenv local $v && make check;
done
cd $test_version_owd
