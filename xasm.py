#!/usr/bin/env python
from __future__ import print_function
from copy import copy
import re
import xdis
# import xdis.bytecode as Mbytecode

class Instruction(object): # (Mbytecode.Instruction):
    def __repr__(self):
        s = ''
        if self.line_no:
            s = "%4d: " % self.line_no
        else:
            s = " " * 6
        s += "%-15s" % self.opname
        if self.arg is not None:
            s += "\t%s" % self.arg
        return s
    pass

def is_int(s):
    try:
        int(s)
        return True
    except:
        return False

def is_lineno(s):
    return re.match('^\d+:', s)

def get_opname_operand(fields):
    assert len(fields) > 0
    if len(fields) > 1:
        if is_int(fields[1]):
            operand = int(fields[1])
        else:
            operand = fields[1]

        return fields[0], operand
    else:
        return fields[0], None

class Assembler(object):
    def __init__(self, Code=None, opc=None):
        self.status = 'unfinished'
        self.Code = Code
        self.opc = opc
        self.instructions = []
        self.bytecode = []
        self.co_argcount = 0
        self.co_kwonlyargcount = 0
        self.co_nlocals = 0
        self.co_stacksize = 10
        self.co_flags = 0
        self.co_code = []
        self.co_consts = []
        self.co_names = []
        self.co_varnames = []
        self.co_filename = 'unknown'
        self.co_name = 'uknown'
        self.co_firstlineno = 1
        self.co_lnotab = ''
        self.co_freevars = tuple()
        self.co_cellvars = tuple()

    def print_instructions(self):
        for inst in self.instructions:
            if inst.line_no:
                print()
            print(inst)

    def err(self, mess):
        print(mess)
        self.status = 'errored'

    def asm(self, path):
        offset = 0
        label = {}
        backpatch_inst = set([])
        opc = self.opc

        self.JREL_INSTRUCTIONS    = set(opc.hasjrel)
        self.JABS_INSTRUCTIONS    = set(opc.hasjabs)
        self.LOOP_INSTRUCTIONS    = set([opc.opmap['SETUP_LOOP']])
        self.JUMP_UNCONDITONAL    = set([opc.opmap['JUMP_ABSOLUTE'],
                                         opc.opmap['JUMP_FORWARD']])
        self.JUMP_INSTRUCTIONS    = self.JABS_INSTRUCTIONS | self.JREL_INSTRUCTIONS | self.LOOP_INSTRUCTIONS | self.JUMP_UNCONDITONAL

        lines = open(path).readlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            i += 1
            if line.startswith('#'):
                if line.startswith('# Python bytecode '):
                    self.version = line[len('# Python bytecode '):].strip().split()[0]
                    # FIXME: check against self.opc.version
                elif line.startswith('# Method Name: '):
                    self.co_name = line[len('# Method Name: '):].strip()
                elif line.startswith('# Filename: '):
                    self.co_filename = line[len('# Filename: '):].strip()
                elif line.startswith('# Argument count: '):
                    l_str = line[len('# Number of locals: '):].strip()
                    self.co_argcount = int(l_str)
                elif line.startswith('# Stack size: '):
                    l_str = line[len('# Number of locals: '):].strip()
                    self.co_stacksize = int(l_str)
                elif line.startswith('# Flags: '):
                    flags = line[len('# Number of locals: '):].strip().split()[0]
                    self.co_flags = eval(flags)
                elif line.startswith('# Constants:'):
                    count = 0
                    while i < len(lines):
                        line = lines[i]
                        i += 1
                        match = re.match('^#\s+(\d+): (.+)$', line)
                        if match:
                            index = int(match.group(1))
                            assert index == count
                            self.co_consts.append(eval(match.group(2)))
                            count += 1
                        else:
                            i -= 1
                            break
                        pass
                    pass
                elif line.startswith('# Names:'):
                    count = 0
                    while i < len(lines):
                        line = lines[i]
                        i += 1
                        match = re.match('^#\s+(\d+): (.+)$', line)
                        if match:
                            index = int(match.group(1))
                            assert index == count
                            self.co_names.append(match.group(2))
                            count += 1
                        else:
                            i -= 1
                            break
                        pass
            else:
                if not line.strip():
                    continue

                match = re.match('^([^\s]+:)$', line)
                if match:
                    label[match.group(1)] = offset
                    continue

                # Opcode section
                fields = line.strip().split()
                line_no = None
                l = len(fields)

                if l > 1:
                    if fields[0] == '>>':
                        fields = fields[1:]
                        l -= 1
                    if is_lineno(fields[0]) and is_int(fields[1]):
                        line_no = int(fields[0][:-1])
                        opname, operand = get_opname_operand(fields[2:])
                    elif is_lineno(fields[0]):
                        line_no = int(fields[0][:-1])
                        fields = fields[1:]
                        if fields[0] == '>>':
                            fields = fields[1:]
                            if is_int(fields[0]):
                                fields = fields[1:]
                        opname, operand = get_opname_operand(fields)
                    elif is_int(fields[0]):
                        opname, operand = get_opname_operand(fields[1:])
                    else:
                        opname, operand = get_opname_operand(fields)
                else:
                    opname = get_opname_operand(fields)

                if opname in opc.opname:
                    inst = Instruction()
                    inst.opname = opname
                    inst.opcode = opc.opmap[opname]
                    if xdis.op_has_argument(inst.opcode, self.opc):
                        inst.arg = operand
                    else:
                        inst.arg = None
                    inst.line_no = line_no
                    self.instructions.append(inst)
                    if inst.opcode in self.JUMP_INSTRUCTIONS:
                        if not is_int(operand):
                            backpatch_inst.add(inst)
                    offset += xdis.op_size(inst.opcode, self.opc)
                pass

            pass

        print('label: ', label)
        print('backpatch: ', backpatch_inst)

        bcode = []
        print(self.instructions)
        for inst in self.instructions:
            bcode.append(inst.opcode)
            if xdis.op_has_argument(inst.opcode, self.opc):
                if inst in backpatch_inst:
                    inst.arg = label[inst.arg]
                if self.opc.version < 3.6:
                    arg_tup = xdis.util.num2code(inst.arg)
                    bcode += arg_tup
                else:
                    bcode.append(inst.arg)

        if xdis.PYTHON3:
            self.co_code = bcode
            args = (self.co_argcount,
                    self.co_nlocals,
                    self.co_stacksize,
                    self.co_kwonlyargcount,
                    self.co_flags,
                    self.co_code,
                    tuple(self.co_consts),
                    tuple(self.co_names),
                    tuple(self.co_varnames),
                    self.co_filename,
                    self.co_name,
                    self.co_firstlineno,
                    self.co_lnotab,
                    self.co_freevars,
                    self.co_cellvars)
        else:
            self.co_code = ''.join([chr(j) for j in bcode])
            args = (self.co_argcount,
                    self.co_nlocals,
                    self.co_stacksize,
                    self.co_flags,
                    self.co_code,
                    tuple(self.co_consts),
                    tuple(self.co_names),
                    tuple(self.co_varnames),
                    self.co_filename,
                    self.co_name,
                    self.co_firstlineno,
                    self.co_lnotab,
                    self.co_freevars,
                    self.co_cellvars)


        # print (*args)
        # co = self.Code(*args)
        import types
        co = types.CodeType(*args)
        return co

from xdis.code import Code2 as Code2
from xdis.opcodes import opcode_27 as opcode27
from xdis.magics import magics

version = '2.7'
a = Assembler(Code2, opcode27)
code = a.asm('tasm.pyasm')
a.print_instructions()
print(code)

# a = Assembler(Code2, opcode27)
# code = a.asm('tasm2.pyasm')
# a.print_instructions()
# print(code)

from struct import pack
with open('tasm.pyc', 'w') as fp:
    fp.write(magics[version])
    import time
    fp.write(pack('I', int(time.time())))
    # In Python 3 you need to write out the size mod 2**32 here
    from xdis.marsh import dumps
    fp.write(dumps(code))
