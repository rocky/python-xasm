#!/usr/bin/env python
from __future__ import print_function
import re, types
import xdis
from xasm.misc import get_opcode

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
    def __init__(self, python_version):
        self.opc, self.Code = get_opcode(python_version)
        self.code_list = []
        self.status = 'unfinished'
        self.python_version = python_version
        self.timestamp = 0

        self.JREL_INSTRUCTIONS    = set(self.opc.hasjrel)
        self.JABS_INSTRUCTIONS    = set(self.opc.hasjabs)
        self.LOOP_INSTRUCTIONS    = set([self.opc.opmap['SETUP_LOOP']])
        self.JUMP_UNCONDITONAL    = set([self.opc.opmap['JUMP_ABSOLUTE'],
                                         self.opc.opmap['JUMP_FORWARD']])
        self.JUMP_INSTRUCTIONS    = (self.JABS_INSTRUCTIONS
                                     | self.JREL_INSTRUCTIONS
                                     | self.LOOP_INSTRUCTIONS
                                     | self.JUMP_UNCONDITONAL)
        self.code = None

    def code_init(self, python_version=None):

        if self.python_version is None and python_version:
            self.python_version = python_version
        # if self.python_version:
        #     if self.python_version >= '3.0':
        #         co_lnotab = b''
        #     else:
        #         co_lnotab = ''
        # else:
        #     co_lnotab = None

        self.code = self.Code(
            co_argcount=0,
            co_kwonlyargcount=0,
            co_nlocals=0,
            co_stacksize=10,
            co_flags=0,
            co_code=[],
            co_consts=[],
            co_names=[],
            co_varnames=[],
            co_filename = 'unknown',
            co_name = 'unknown',
            co_firstlineno=1,
            co_lnotab = [],
            co_freevars = tuple(),
            co_cellvars = tuple())

        self.code.instructions = []

    def print_instructions(self):
        for inst in self.code.instructions:
            if inst.line_no:
                print()
            print(inst)

    def err(self, mess):
        print(mess)
        self.status = 'errored'

def asm_file(path):
    offset = 0
    label = {}
    backpatch_inst = set([])
    methods = {}
    method_name = None
    asm = None

    lines = open(path).readlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith('#'):
            if line.startswith('# Python bytecode '):
                python_version = line[len('# Python bytecode '):].strip().split()[0]
                asm = Assembler(python_version)
                asm.code_init()
            elif line.startswith('# Timestamp in code: '):
                text = line[len('# Timestamp in code: '):].strip()
                time_str = text.split()[0]
                if is_int(time_str):
                    asm.timestamp = int(time_str)
            elif line.startswith('# Method Name: '):
                if method_name:
                    co = create_code(asm, label, backpatch_inst)
                    asm.code_list.append(co)
                    methods[method_name] = co
                    offset = 0
                    label = {}
                    backpatch_inst = set([])
                asm.code_init()
                asm.code.co_name = line[len('# Method Name: '):].strip()
                method_name = asm.code.co_name

            elif line.startswith('# Filename: '):
                asm.code.co_filename = line[len('# Filename: '):].strip()
            elif line.startswith('# First Line: '):
                s = line[len('# First Line: '):].strip()
                first_lineno = int(s)
                asm.code.co_firstlineno = first_lineno
                asm.code.co_lnotab.append((0, first_lineno))
            elif line.startswith('# Argument count: '):
                argc = line[len('# Argument count: '):].strip().split()[0]
                asm.code.co_argcount = eval(argc)
            elif line.startswith('# Number of locals: '):
                l_str = line[len('# Number of locals: '):].strip()
                asm.code.co_nlocals = int(l_str)
            elif line.startswith("# Source code size mod 2**32: "):
                l_str = line[len("# Source code size mod 2**32: "):-len(' bytes')].strip()
                asm.size = int(l_str)
            elif line.startswith('# Stack size: '):
                l_str = line[len('# Stack size: '):].strip()
                asm.code.co_stacksize = int(l_str)
            elif line.startswith('# Flags: '):
                flags = line[len('# Flags: '):].strip().split()[0]
                asm.code.co_flags = eval(flags)
            elif line.startswith('# Constants:'):
                count = 0
                while i < len(lines):
                    line = lines[i]
                    i += 1
                    match = re.match('^#\s+(\d+): (.+)$', line)
                    if match:
                        index = int(match.group(1))
                        assert index == count
                        expr = match.group(2)
                        match = re.match('<code object (\S+) at', expr)
                        if match:
                            name = match.group(1)
                            asm.code.co_consts.append(methods[name])
                        else:
                            asm.code.co_consts.append(eval(expr))
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
                        asm.code.co_names.append(match.group(2))
                        count += 1
                    else:
                        i -= 1
                        break
                    pass
            elif line.startswith('# Positional arguments:'):
                line = lines[i]
                asm.code.co_varnames = line[1:].strip().split(', ')
                i += 1
        else:
            if not line.strip():
                continue

            match = re.match('^([^\s]+):$', line)
            if match:
                label[match.group(1)] = offset
                continue

            match = re.match('^\s*([\d]+):\s*$', line)
            if match:
                line_no = int(match.group(1))
                asm.code.co_lnotab.append((offset, line_no))
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
                opname, _ = get_opname_operand(fields)

            if opname in asm.opc.opname:
                inst = Instruction()
                inst.opname = opname
                inst.opcode = asm.opc.opmap[opname]
                if xdis.op_has_argument(inst.opcode, asm.opc):
                    inst.arg = operand
                else:
                    inst.arg = None
                inst.line_no = line_no
                asm.code.instructions.append(inst)
                if inst.opcode in asm.JUMP_INSTRUCTIONS:
                    if not is_int(operand):
                        backpatch_inst.add(inst)
                offset += xdis.op_size(inst.opcode, asm.opc)
            else:
                raise RuntimeError("Illegal opname %s in: %s" %
                                   (opname, line))
            pass
        pass
    if asm:
        asm.code_list.append(create_code(asm, label, backpatch_inst))
    asm.code_list.reverse()
    return asm

def create_code(asm, label, backpatch_inst):
    print('label: ', label)
    print('backpatch: ', backpatch_inst)

    bcode = []
    print(asm.code.instructions)

    offset = 0
    for inst in asm.code.instructions:
        bcode.append(inst.opcode)
        offset += xdis.op_size(inst.opcode, asm.opc)
        if xdis.op_has_argument(inst.opcode, asm.opc):
            if inst in backpatch_inst:
                target = inst.arg
                int_target = is_int(target)
                try:
                    if inst.opcode in asm.JREL_INSTRUCTIONS and int_target:
                        inst.arg = offset + label[target]
                    else:
                        inst.arg = label[target]
                        pass
                    pass
                except KeyError:
                    raise RuntimeError("Label %s not found. Instruction:\n%s" %
                                       (target, inst))

            if asm.opc.version < 3.6:
                arg_tup = xdis.util.num2code(inst.arg)
                bcode += arg_tup
            else:
                bcode.append(inst.arg)

    if asm.python_version >= '3.0':
        co_code = bytearray()
        for j in bcode:
            co_code.append(j)
        asm.code.co_code = bytes(co_code)
        code = asm.code.freeze()
    else:
        asm.code.co_code = ''.join([chr(j) for j in bcode])
        code = asm.code.freeze()

    asm.print_instructions()
    asm.code = None

    # print (*args)
    # co = self.Code(*args)
    return code
