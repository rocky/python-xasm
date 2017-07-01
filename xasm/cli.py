#!/usr/bin/env python
from xasm.assemble import asm
from xasm.misc import get_opcode, write_pycfile

import click
@click.command()
@click.option("--python-version", default=None)
@click.option("--asm-file", default='./tasm.pyasm')
@click.option("--pyc-file", default=None)
def main(asm_file, python_version, pyc_file):
    if python_version:
        opc, Code = get_opcode(python_version)
    else:
        opc, Code = None, None
    code_list, timestamp, python_version = asm(asm_file, Code, opc)
    print(code_list)

    # a = Assembler(Code2, opcode27)
    # code = a.asm('tasm2.pyasm')
    # a.print_instructions()
    # print(code)
    if not pyc_file and asm_file.endswith('.pyasm'):
        pyc_file = asm_file[:-len('.pyasm')] + '.pyc'

    write_pycfile(pyc_file, python_version, code_list, timestamp)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
