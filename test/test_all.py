#!/usr/bin/env python

import os, subprocess, sys
import os.path as osp

os.chdir(osp.dirname(__file__))

def test_xasm():
    python_interp = sys.executable
    for asm in "tasm fn gcd columnize".split():
        print("Testing %s" % asm)
        assert subprocess.call((python_interp, "./%s.py" % asm)) == 0

if __name__ == "__main__":
    test_xasm()
