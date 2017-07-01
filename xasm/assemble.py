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
        if xdis.PYTHON3:
            self.co_lnotab = b''
        else:
            self.co_lnotab = ''
        self.co_freevars = tuple()
        self.co_cellvars = tuple()

        self.JREL_INSTRUCTIONS    = set(opc.hasjrel)
        self.JABS_INSTRUCTIONS    = set(opc.hasjabs)
        self.LOOP_INSTRUCTIONS    = set([opc.opmap['SETUP_LOOP']])
        self.JUMP_UNCONDITONAL    = set([opc.opmap['JUMP_ABSOLUTE'],
                                         opc.opmap['JUMP_FORWARD']])
        self.JUMP_INSTRUCTIONS    = self.JABS_INSTRUCTIONS | self.JREL_INSTRUCTIONS | self.LOOP_INSTRUCTIONS | self.JUMP_UNCONDITONAL

    def print_instructions(self):
        for inst in self.instructions:
            if inst.line_no:
                print()
            print(inst)

    def err(self, mess):
        print(mess)
        self.status = 'errored'

def asm(path, Code, opc):
    code_list = []
    offset = 0
    label = {}
    backpatch_inst = set([])
    version = None
    methods = {}
    method_name = None
    timestamp = 0

    asm = None

    lines = open(path).readlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith('#'):
            if line.startswith('# Python bytecode '):
                python_version = line[len('# Python bytecode '):].strip().split()[0]
                opc, Code = get_opcode(python_version)
            elif line.startswith('# Timestamp in code: '):
                text = line[len('# Timestamp in code: '):].strip()
                time_str = text.split()[0]
                if is_int(time_str):
                    timestamp = int(time_str)
            elif line.startswith('# Method Name: '):
                if asm:
                    co = create_code(asm, label, backpatch_inst)
                    code_list.append(co)
                    methods[method_name] = co
                    offset = 0
                    label = {}
                    backpatch_inst = set([])

                asm = Assembler(Code, opc)
                asm.version = version
                asm.co_name = line[len('# Method Name: '):].strip()
                method_name = asm.co_name

            elif line.startswith('# Filename: '):
                asm.co_filename = line[len('# Filename: '):].strip()
            elif line.startswith('# Argument count: '):
                argc = line[len('# Argument count: '):].strip().split()[0]
                asm.argc = eval(argc)
            elif line.startswith('# Number of locals: '):
                l_str = line[len('# Number of locals: '):].strip()
                asm.nlocals = int(l_str)
            elif line.startswith('# Stack size: '):
                l_str = line[len('# Stack size: '):].strip()
                asm.co_stacksize = int(l_str)
            elif line.startswith('# Flags: '):
                flags = line[len('# Flags: '):].strip().split()[0]
                asm.co_flags = eval(flags)
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
                            asm.co_consts.append(methods[name])
                        else:
                            asm.co_consts.append(eval(expr))
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
                        asm.co_names.append(match.group(2))
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
                if xdis.op_has_argument(inst.opcode, asm.opc):
                    inst.arg = operand
                else:
                    inst.arg = None
                inst.line_no = line_no
                asm.instructions.append(inst)
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
        code_list.append(create_code(asm, label, backpatch_inst))
    code_list.reverse()
    return code_list, timestamp, python_version

def create_code(asm, label, backpatch_inst):
    print('label: ', label)
    print('backpatch: ', backpatch_inst)

    bcode = []
    print(asm.instructions)

    offset = 0
    for inst in asm.instructions:
        bcode.append(inst.opcode)
        offset += xdis.op_size(inst.opcode, asm.opc)
        if xdis.op_has_argument(inst.opcode, asm.opc):
            if inst in backpatch_inst:
                if inst.opcode in asm.JREL_INSTRUCTIONS:
                    inst.arg = offset + label[inst.arg]
                else:
                    inst.arg = label[inst.arg]
            if asm.opc.version < 3.6:
                arg_tup = xdis.util.num2code(inst.arg)
                bcode += arg_tup
            else:
                bcode.append(inst.arg)

    if xdis.PYTHON3:
        co_code = bytearray()
        for j in bcode:
            co_code.append(j)
        asm.co_code = bytes(co_code)
        args = (asm.co_argcount,
                asm.co_nlocals,
                asm.co_stacksize,
                asm.co_kwonlyargcount,
                asm.co_flags,
                asm.co_code,
                tuple(asm.co_consts),
                tuple(asm.co_names),
                tuple(asm.co_varnames),
                asm.co_filename,
                asm.co_name,
                asm.co_firstlineno,
                asm.co_lnotab,
                asm.co_freevars,
                asm.co_cellvars)
    else:
        asm.co_code = ''.join([chr(j) for j in bcode])
        args = (asm.co_argcount,
                asm.co_nlocals,
                asm.co_stacksize,
                asm.co_flags,
                asm.co_code,
                tuple(asm.co_consts),
                tuple(asm.co_names),
                tuple(asm.co_varnames),
                asm.co_filename,
                asm.co_name,
                asm.co_firstlineno,
                asm.co_lnotab,
                asm.co_freevars,
                asm.co_cellvars)

    asm.print_instructions()

    # print (*args)
    # co = self.Code(*args)
    return types.CodeType(*args)
