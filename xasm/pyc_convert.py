#!/usr/bin/env python
"""Convert Python 2.6 bytecode to Python 2.7"""
from xdis.main import disassemble_file
import xdis
from xasm.misc import write_pycfile
from xdis.opcodes import opcode_27
from tempfile import NamedTemporaryFile
import os.path as osp
import os
from copy import copy
from xasm.assemble import asm_file, Assembler, create_code
import click

def xlate26_27(inst):
    """Between 2.6 and 2.7 opcode values changed
    Adjust for the differences by using the opcode name
    """
    inst.opcode = opcode_27.opmap[inst.opname]

def conversion_to_version(conversion_type, is_dest=False):
    if is_dest:
        return conversion_type[-2] + '.' + conversion_type[-1]
    else:
        return conversion_type[0] + '.' + conversion_type[1]


def transform_asm(asm, conversion_type, dest_version):

    new_asm = Assembler(dest_version)
    new_asm.code = copy(asm.code)

    for j, code in enumerate(asm.code_list):
        offset2label = {v: k for k, v in asm.label[j].items()}
        new_asm.codes = copy(asm.codes)
        new_asm.backpatch.append(copy(asm.backpatch[j]))
        new_asm.label.append(copy(asm.label[j]))
        new_asm.codes.append(copy(code))
        i = 0
        instructions = asm.codes[j].instructions
        new_asm.code.instructions = []
        n = len(instructions)
        offset = 0
        while i < n:
            inst = instructions[i]
            new_inst = copy(inst)
            # Change JUMP_IF_FALSE and JUMP_IF_TRUE to
            # POP_JUMP_IF_FALSE and POP_JUMP_IF_TRUE
            if inst.opname in ('JUMP_IF_FALSE', 'JUMP_IF_TRUE'):
                i += 1
                assert i < n
                assert instructions[i].opname == 'POP_TOP'
                new_inst.offset = offset
                new_inst.opname = (
                    'POP_JUMP_IF_FALSE' if inst.opname == 'JUMP_IF_FALSE' else 'POP_JUMP_IF_TRUE'
                )
                new_asm.backpatch[-1].remove(inst)
                new_inst.arg = 'L%d' % (inst.offset + inst.arg + 3)
                new_asm.backpatch[-1].add(new_inst)
            else:
                xlate26_27(new_inst)

            if inst.offset in offset2label:
                new_asm.label[-1][offset2label[inst.offset]] = offset
            offset += xdis.op_size(new_inst.opcode, opcode_27)
            new_asm.code.instructions.append(new_inst)
            i += 1
            pass

    co = create_code(new_asm, new_asm.label[-1], new_asm.backpatch[-1])
    new_asm.code_list.append(co)
    new_asm.code_list.reverse()
    new_asm.finished = 'finished'
    return new_asm

@click.command()
@click.option('--conversion-type', '-t', type=click.Choice(['26-27', '25-26']),
              help='specify conversion from/to bytecode', default='26-27')
@click.argument('input_pyc', type=click.Path('r'), nargs=1)
@click.argument('output_pyc', type=click.Path('w'),
                required=False, nargs=1, default=None)
def main(conversion_type, input_pyc, output_pyc):
    """Convert Python bytecode from one version to another.

    INPUT_PYC contains the input bytecode path name
    OUTPUT_PYC  contians the output bytecode path name if supplied
    The --conversion type option specifies what conversion to do.

    Note: there are a very limited set of conversions currently supported.
    Help out and write more!"""

    shortname = osp.basename(input_pyc)
    if shortname.endswith('.pyc'):
        shortname = shortname[:-4]
    src_version = conversion_to_version(conversion_type, is_dest=False)
    dest_version = conversion_to_version(conversion_type, is_dest=True)
    if output_pyc is None:
        output_pyc = "%s-%s.pyc" % (shortname, dest_version)
    temp_asm = NamedTemporaryFile('w', suffix='.pyasm', prefix=shortname, delete=False)
    (filename, co, version,
     timestamp, magic_int) = disassemble_file(input_pyc, temp_asm, asm_format=True)
    temp_asm.close()
    assert version == float(src_version), (
        "Need Python %s bytecode; got bytecode for version %s" %
        (src_version, version))
    asm = asm_file(temp_asm.name)
    new_asm = transform_asm(asm, conversion_type, dest_version)
    os.unlink(temp_asm.name)
    write_pycfile(output_pyc, new_asm)

if __name__ == '__main__':
    main()
