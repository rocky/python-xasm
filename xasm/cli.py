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
    if os.stat(asm_path).st_size == 0:
        print("Size of assembly file %s is zero" % asm_path)
        sys.exit(1)
    asm = asm_file(asm_path)

    if not pyc_file and asm_path.endswith('.pyasm'):
        pyc_file = asm_path[:-len('.pyasm')] + '.pyc'

    write_pycfile(pyc_file, asm)

if __name__ == '__main__':
    main(sys.argv[1:])
