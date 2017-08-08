#!/usr/bin/env python
"""Convert Python 2.6 bytecode to Python 2.7"""
from xdis.main import disassemble_file
import xdis
from xdis.opcodes import opcode_27
from tempfile import NamedTemporaryFile
import os.path as osp
import os
from copy import copy
from xasm.assemble import asm_file, Assembler, create_code

import sys

def transform_asm(asm):
    new_asm = Assembler('2.7')
    new_asm.code_init()

    new_asm.backpatch_inst = asm.backpatch_inst
    new_asm.label = copy(asm.label)
    for code in asm.code_list:
        new_asm.code_list.append(copy(code))
        i = 0
        instructions = code.instructions
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
            # FIXME if inst.offset is in a label, then adjust the label
            offset += xdis.op_size(new_inst.opcode, opcode_27)
            new_asm.code.instructions.append(new_inst)
            i += 1
            pass

    new_asm.code_list.append(create_code(new_asm))
    new_asm.code_list.reverse()
    new_asm.finished = 'finished'
    return new_asm


if len(sys.argv) != 2:
    print("usage: %s bytecode-26 bytecode27" % sys.argv[0])
bytecode_26_path, bytecode_27_path = sys.argv[1:3]


shortname = osp.basename(bytecode_26_path)
temp26_asm = NamedTemporaryFile('w', suffix='.pyasm26', prefix=shortname, delete=False)
filename, co, version, timestamp, magic_int = disassemble_file(bytecode_26_path,
                                                               temp26_asm, asm_format=True)
temp26_asm.close()
assert version == 2.6, "Need a Python 2.6 bytecode; got bytecode for version %s" % version
asm = asm_file(temp26_asm.name)
new_asm = transform_asm(asm)
os.unlink(temp26_asm.name)
