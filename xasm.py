#!/usr/bin/env python
import re
from xdis.code import Code2 as Code
# import xdis.bytecode as Mbytecode

from xdis.opcodes import opcode_27 as opc

class Instruction(object): # (Mbytecode.Instruction):
    def __repr__(self):
        s = ''
        if self.line_no:
            s = "%4d: " % self.line_no
        else:
            s = " " * 6
        return "%s%s" % (s, self.opname)
    pass

def is_int(s):
    try:
        int(s)
        return True
    except:
        return False

def get_opname_operand(a):
    try:
        assert len(a) > 0
    except:
        from trepan.api import debug; debug()
    if len(a) > 1:
        return a[0], a[1]
    else:
        return a[0]

def asm(path):
    co_argcount = 0
    co_kwonlyargcount = 0
    co_nlocals = None
    co_stacksize = 10
    co_flags = 0
    co_code = []
    co_consts = []
    co_names = []
    co_varnames = []
    co_filename = 'unknown'
    co_name = 'uknown'
    co_firstlineno = 1
    co_lnotab = []
    co_freevars = tuple()
    co_cellvars = tuple()

    lines = open(path).readlines()
    instructions = []
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith('#'):
            if line.startswith('# Filename: '):
                co_filename = line[len('# Filename: '):].strip()
            elif line.startswith('# Method Name: '):
                co_name = line[len('# Method Name: '):].strip()
            elif line.startswith('# Argument count: '):
                l_str = line[len('# Number of locals: '):].strip()
                co_argcount = int(l_str)
            elif line.startswith('# Stack size: '):
                l_str = line[len('# Number of locals: '):].strip()
                co_stacksize = int(l_str)
            elif line.startswith('# Flags: '):
                flags = line[len('# Number of locals: '):].strip().split()[0]
                co_flags = eval(flags)
            elif line.startswith('# Constants:'):
                count = 0
                while i < len(lines):
                    line = lines[i]
                    i += 1
                    match = re.match('^#\s+(\d+): (.+)$', line)
                    if match:
                        index = int(match.group(1))
                        assert index == count
                        co_consts.append(eval(match.group(2)))
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
                        co_names.append(match.group(2))
                        count += 1
                    else:
                        i -= 1
                        break
                    pass
        else:
            if not line.strip():
                continue
            # Opcode section
            fields = line.strip().split()
            line_no = None
            if len(fields) > 2:
                if is_int(fields[0]) and is_int(fields[1]):
                    line_no = int(fields[0])
                    opname, operand = get_opname_operand(fields[2:])
                elif is_int(fields[0]):
                    opname, operand = get_opname_operand(fields[1:])
                else:
                    opname, operand = get_opname_operand(fields)
            else:
                opname, operand = get_opname_operand(fields)
            if opname in opc.opname:
                inst = Instruction()
                inst.opname = opname
                inst.opcode = opc.opmap[opname]
                inst.arg = operand
                inst.line_no = line_no
                instructions.append(inst)
            pass

        pass

    print (co_argcount,
           co_kwonlyargcount,
           co_nlocals,
           co_stacksize,
           co_flags,
           co_code,
           co_consts,
           co_names,
           co_varnames,
           co_filename,
           co_name,
           co_firstlineno,
           co_lnotab,
           co_freevars,
           co_cellvars)
    for i in instructions:
        print(i)


    code = Code(co_argcount,
                co_kwonlyargcount,
                co_nlocals,
                co_stacksize,
                co_flags,
                co_code,
                co_consts,
                co_names,
                co_varnames,
                co_filename,
                co_name,
                co_firstlineno,
                co_lnotab,
                co_freevars,
                co_cellvars)
    return code

code = asm('tasm.pyasm')
print(code)
