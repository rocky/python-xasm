#!/usr/bin/env python
from xasm.assemble import asm
from xasm.pythonfile import write_pycfile

import click
@click.command()
@click.option("--python-version", default='2.7')
@click.option("--asm-file", default='./tasm.pyasm')
@click.option("--pyc-file", default=None)
def main(asm_file, python_version, pyc_file):
    if python_version in "2.5 2.6 2.7".split():
        from xdis.code import Code2 as Code
        if python_version == '2.5':
            from xdis.opcodes import opcode_25 as opc
        elif python_version == '2.6':
            from xdis.opcodes import opcode_26 as opc
        else:
            from xdis.opcodes import opcode_27 as opc
            pass
    elif python_version in "3.3 3.4".split():
        from xdis.code import Code3 as Code
        if python_version == '3.4':
            from xdis.opcodes import opcode_33 as opc
        elif python_version == '3.4':
            from xdis.opcodes import opcode_34 as opc
    else:
        raise RuntimeError("Python version %s not supported yet" % python_version)

    code_list, timestamp = asm(Code, opc, asm_file)
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
