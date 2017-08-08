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

import sys

def xlate26_27(inst):
    """Between 2.6 and 2.7 opcode values changed
    Adjust for the differences by using the opcode name
    """
    inst.opcode = opcode_27.opmap[inst.opname]

def transform_asm(asm):
    new_asm = Assembler('2.7')
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
write_pycfile(bytecode_27_path, new_asm)
