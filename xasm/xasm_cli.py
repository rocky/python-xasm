#!/usr/bin/env python
from __future__ import print_function
import click, os, sys
from xasm.assemble import asm_file
from xasm.misc import write_pycfile

@click.command()
@click.option("--pyc-file", default=None)
@click.argument("asm-path", type=click.Path(exists=True, readable=True),
		 required=True)
def main(pyc_file, asm_path):
    """
    Create Python bytecode from a Python assembly file.

    ASM_PATH gives the input Python assembly file. We suggest ending the
    file in .pyc

    If --pyc-file is given, that indicates the path to write the
    Python bytecode. The path should end in '.pyc'.

    See https://github.com/rocky/python-xasm/blob/master/HOW-TO-USE.rst
    for how to write a Python assembler file.
    """
    if os.stat(asm_path).st_size == 0:
        print("Size of assembly file %s is zero" % asm_path)
        sys.exit(1)
    asm = asm_file(asm_path)

    if not pyc_file and asm_path.endswith('.pyasm'):
        pyc_file = asm_path[:-len('.pyasm')] + '.pyc'

    write_pycfile(pyc_file, asm)

if __name__ == '__main__':
    main(sys.argv[1:])
