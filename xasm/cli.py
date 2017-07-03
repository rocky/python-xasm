#!/usr/bin/env python
from xasm.assemble import asm_file
from xasm.misc import write_pycfile

import click
@click.command()
@click.option("--path", default='./tasm.pyasm')
@click.option("--pyc-file", default=None)
def main(path, pyc_file):
    asm = asm_file(path)

    if not pyc_file and path.endswith('.pyasm'):
        pyc_file = path[:-len('.pyasm')] + '.pyc'

    write_pycfile(pyc_file, asm)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
