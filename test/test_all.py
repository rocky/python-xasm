#!/usr/bin/env python

import os
import os.path as osp
import subprocess
import sys

os.chdir(osp.dirname(__file__))


def test_xasm() -> None:
    python_interp = sys.executable
    for asm in "tasm fn gcd columnize".split():
        print("Testing %s" % asm)
        assert subprocess.call((python_interp, "./%s.py" % asm)) == 0


if __name__ == "__main__":
    test_xasm()
