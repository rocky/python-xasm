#!/usr/bin/env python
import ast, re, xdis
from xdis.opcodes.base import cmp_op
from xdis import get_opcode, load_module
from xdis.version_info import PYTHON_VERSION_TRIPLE, version_str_to_tuple

# import xdis.bytecode as Mbytecode

class Instruction(object):  # (Mbytecode.Instruction):
    def __repr__(self):
        s = ""
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
    except ValueError:
        return False


def is_lineno(s):
    return re.match(r"^\d+:", s)


def get_opname_operand(opc, fields):
    assert len(fields) > 0
    opname = fields[0]
    if opc.opmap[opname] < opc.HAVE_ARGUMENT:
        return opname, None
    if len(fields) > 1:
        if is_int(fields[1]):
            operand = int(fields[1])
        else:
            operand = ' '.join(fields[1:])
            if operand.startswith("(to "):
                int_val = operand[len("(to "):]
                # In xasm format this shouldn't appear
                if is_int(int_val):
                    operand = int(int_val)

        return opname, operand
    else:
        return opname, None


class Assembler(object):
    def __init__(self, python_version, is_pypy):
        self.opc = get_opcode(python_version, is_pypy)
        self.code_list = []
        self.codes = []  # FIXME use a better name
        self.status = "unfinished"
        self.size = 0  # Size of source code. Only relevant in version 3 and above
        self.python_version = python_version
        self.timestamp = None
        self.backpatch = []  # list of backpatch dicts, one for each function
        self.label = []  # list of label dists, one for each function
        self.code = None
        self.siphash = None

    def code_init(self, python_version=None):

        if self.python_version is None and python_version:
            self.python_version = python_version

        self.code = xdis.codetype.to_portable(
            co_argcount=0,
            co_posonlyargcount=0,
            co_kwonlyargcount=0,
            co_nlocals=0,
            co_stacksize=10,
            co_flags=0,
            co_code=[],
            co_consts=[],
            co_names=[],
            co_varnames=[],
            co_filename="unknown",
            co_name="unknown",
            co_firstlineno=1,
            co_lnotab={},
            co_freevars=[],
            co_cellvars=[],
            version_triple=python_version,
        )

        self.code.instructions = []

    def update_lists(self, co, label, backpatch):
        self.code_list.append(co)
        self.codes.append(self.code)
        self.label.append(label)
        self.backpatch.append(backpatch)

    def print_instructions(self):
        for inst in self.code.instructions:
            if inst.line_no:
                print()
            print(inst)

    def err(self, mess):
        print(mess)
        self.status = "errored"


def asm_file(path):
    offset = 0
    methods = {}
    method_name = None
    asm = None
    backpatch_inst = set([])
    label = {}
    python_version = None
    lines = open(path).readlines()
    i = 0
    bytecode_seen = False
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith(".READ"):
            match = re.match("^.READ (.+)$", line)
            if match:
                input_pyc = match.group(1)
                print(f"Reading {input_pyc}")
                (version, timestamp, magic_int, co, is_pypy, source_size, sip_hash) = load_module(
                    input_pyc
                )
                if python_version and python_version != version:
                    TypeError(
                        f"We previously saw Python version {python_version} but we just loaded {version}.\n"
                    )
                python_version = version
                # FIXME: extract all code options below the top-level and asm.code_list

        elif line.startswith("#"):
            match = re.match("^# (Pypy )?Python bytecode ", line)
            if match:
                if match.group(1):
                    pypy_str = match.group(1)
                    is_pypy = len(pypy_str)
                else:
                    is_pypy = False
                    pypy_str = ""

                version = (
                    line[len("# Python bytecode " + pypy_str) :].strip().split()[0]
                )

                python_version_pair = version_str_to_tuple(python_version, len=2)
                asm = Assembler(python_version_pair, is_pypy)
                if python_version_pair >= (3, 10):
                    TypeError(
                        f"Creating Python version {python_version} not supported yet. Feel free to fix and put in a PR.\n"
                    )
                asm.code_init(python_version_pair)
                bytecode_seen = True
            elif line.startswith("# Timestamp in code: "):
                text = line[len("# Timestamp in code: ") :].strip()
                time_str = text.split()[0]
                if is_int(time_str):
                    asm.timestamp = int(time_str)
            elif line.startswith("# Method Name: "):
                if method_name:
                    co = create_code(asm, label, backpatch_inst)
                    asm.update_lists(co, label, backpatch_inst)
                    label = {}
                    backpatch_inst = set([])
                    methods[method_name] = co
                    offset = 0
                python_version_pair = version_str_to_tuple(python_version, len=2)
                asm.code_init(python_version_pair)
                asm.code.co_name = line[len("# Method Name: ") :].strip()
                method_name = asm.code.co_name
            elif line.startswith("# SipHash: "):
                siphash = line[len("# ShipHash: ") :].strip().split()[0]
                asm.siphash = ast.literal_eval(siphash)
                if asm.siphash != 0:
                    raise TypeError(
                        "SIP hashes not supported yet. Feel free to fix and in a PR.\n"
                    )

            elif line.startswith("# Filename: "):
                asm.code.co_filename = line[len("# Filename: ") :].strip()
            elif line.startswith("# First Line: "):
                s = line[len("# First Line: ") :].strip()
                first_lineno = int(s)
                asm.code.co_firstlineno = first_lineno
            elif line.startswith("# Argument count: "):
                argc = line[len("# Argument count: ") :].strip().split()[0]
            elif line.startswith("# Position-only argument count: "):
                argc = (
                    line[len("# Position-only argument count: ") :].strip().split()[0]
                )
                asm.code.co_posonlyargcount = ast.literal_eval(argc)
            elif line.startswith("# Keyword-only argument count: "):
                argc = line[len("# Keyword-only argument count: ") :].strip().split()[0]
                asm.code.co_kwonlyargcount = ast.literal_eval(argc)
            elif line.startswith("# Number of locals: "):
                l_str = line[len("# Number of locals: ") :].strip()
                asm.code.co_nlocals = int(l_str)
            elif line.startswith("# Source code size mod 2**32: "):
                l_str = line[
                    len("# Source code size mod 2**32: ") : -len(" bytes")
                ].strip()
                asm.size = int(l_str)
            elif line.startswith("# Stack size: "):
                l_str = line[len("# Stack size: ") :].strip()
                asm.code.co_stacksize = int(l_str)
            elif line.startswith("# Flags: "):
                flags = line[len("# Flags: ") :].strip().split()[0]
                asm.code.co_flags = ast.literal_eval(flags)
            elif line.startswith("# Constants:"):
                count = 0
                while i < len(lines):
                    line = lines[i]
                    i += 1
                    match = re.match(r"^#\s+(\d+): (.+)$", line)
                    if match:
                        index = int(match.group(1))
                        assert index == count, (
                            "Constant index {%d} found on line {%d}"
                            "doesn't match expected constant index {%d}."
                            % (index, i, count)
                        )
                        expr = match.group(2)
                        match = re.match(
                            r"<(?:Code\d+ )?code object (\S+) at (0x[0-f]+)", expr
                        )
                        if match:
                            name = match.group(1)
                            m2 = re.match("^<(.+)>$", name)
                            if m2:
                                name = "%s_%s" % (m2.group(1), match.group(2))
                            if name in methods:
                                asm.code.co_consts.append(methods[name])
                            else:
                                print(
                                    f"line {i} ({asm.code.co_filename}, {method_name}): can't find method {name}"
                                )
                                bogus_name = f"**bogus {name}**"
                                print(f"\t appending {bogus_name} to list of constants")
                                asm.code.co_consts.append()
                        else:
                            asm.code.co_consts.append(ast.literal_eval(expr))
                        count += 1
                    else:
                        i -= 1
                        break
                    pass
                pass
            elif line.startswith("# Cell variables:"):
                i = update_code_tuple_field("co_cellvars", asm.code, lines, i)
            elif line.startswith("# Free variables:"):
                i = update_code_tuple_field("co_freevars", asm.code, lines, i)
            elif line.startswith("# Names:"):
                i = update_code_tuple_field("co_names", asm.code, lines, i)
            elif line.startswith("# Varnames:"):
                line = lines[i]
                asm.code.co_varnames = line[1:].strip().split(", ")
                i += 1
            elif line.startswith("# Positional arguments:"):
                line = lines[i]
                args = line[1:].strip().split(", ")
                asm.code.co_argcount = len(args)
                i += 1
        else:
            if not line.strip():
                continue

            match = re.match(r"^([^\s]+):$", line)
            if match:
                label[match.group(1)] = offset
                continue

            match = re.match(r"^\s*([\d]+):\s*$", line)
            if match:
                line_no = int(match.group(1))
                asm.code.co_lnotab[offset] = line_no
                continue

            # Opcode section
            assert (
                bytecode_seen
            ), "File needs to start out with: # Python bytecode <version>"
            fields = line.strip().split()
            line_no = None
            num_fields = len(fields)

            if num_fields > 1:
                if fields[0] == ">>":
                    fields = fields[1:]
                    num_fields -= 1
                if is_lineno(fields[0]) and is_int(fields[1]):
                    line_no = int(fields[0][:-1])
                    opname, operand = get_opname_operand(asm.opc, fields[2:])
                elif is_lineno(fields[0]):
                    line_no = int(fields[0][:-1])
                    fields = fields[1:]
                    if fields[0] == ">>":
                        fields = fields[1:]
                        if is_int(fields[0]):
                            fields = fields[1:]
                    opname, operand = get_opname_operand(asm.opc, fields)
                elif is_int(fields[0]):
                    opname, operand = get_opname_operand(asm.opc, fields[1:])
                else:
                    opname, operand = get_opname_operand(asm.opc, fields)
            else:
                opname, _ = get_opname_operand(asm.opc, fields)

            if opname in asm.opc.opname:
                inst = Instruction()
                inst.opname = opname.replace("+", "_")
                inst.opcode = asm.opc.opmap[inst.opname]
                if xdis.op_has_argument(inst.opcode, asm.opc):
                    inst.arg = operand
                else:
                    inst.arg = None
                inst.line_no = line_no
                asm.code.instructions.append(inst)
                if inst.opcode in asm.opc.JUMP_OPS:
                    if not is_int(operand):
                        backpatch_inst.add(inst)
                offset += xdis.op_size(inst.opcode, asm.opc)
            else:
                raise RuntimeError("Illegal opname %s in:\n%s" % (opname, line))
            pass
        pass
    # print(asm.code.co_lnotab)
    if asm:
        co = create_code(asm, label, backpatch_inst)
        asm.update_lists(co, label, backpatch_inst)
    asm.code_list.reverse()
    asm.status = "finished"
    return asm


def member(fields, match_value):
    for i, v in enumerate(fields):
        if v == match_value and type(v) == type(match_value):
            return i
        pass
    return -1


def update_code_field(field_name, value, inst, opc):
    field_values = getattr(opc, field_name)
    # Can't use "in" because True == 1 and False == 0
    # if value in l:
    i = member(field_values, value)
    if i >= 0:
        inst.arg = i
    else:
        inst.arg = len(field_values)
        field_values.append(value)


def update_code_tuple_field(field_name, code, lines, i):
    count = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        match = re.match(r"^#\s+(\d+): (.+)$", line)
        if match:
            index = int(match.group(1))
            assert index == count
            field_values = getattr(code, field_name)
            field_values.append(match.group(2))
            count += 1
        else:
            i -= 1
            break
        pass
    pass
    return i


def err(msg, inst, i):
    msg += ". Instruction %d:\n%s" % (i, inst)
    raise RuntimeError(msg)


def decode_lineno_tab(lnotab, first_lineno):

    line_number, line_number_diff = first_lineno, 0
    offset, offset_diff = 0, 0
    uncompressed_lnotab = {}
    for i in range(0, len(lnotab), 2):
        offset_diff = lnotab[i]
        line_number_diff = lnotab[i + 1]
        if not isinstance(offset_diff, int):
            offset_diff = ord(offset_diff)
            line_number_diff = ord(line_number_diff)

        assert offset_diff < 256
        if offset_diff == 255:
            continue
        assert line_number_diff < 256
        if line_number_diff == 255:
            continue
        line_number += line_number_diff
        offset += offset_diff
        line_number_diff, offset_diff = 0, 0
        uncompressed_lnotab[offset] = line_number

    return uncompressed_lnotab


def create_code(asm, label, backpatch):
    # print('label: ', asm.label)
    # print('backpatch: ', asm.backpatch_inst)

    bcode = []
    # print(asm.code.instructions)

    offset = 0
    extended_value = 0
    offset2label = {label[j]: j for j in label}

    for i, inst in enumerate(asm.code.instructions):
        bcode.append(inst.opcode)
        if offset in offset2label:
            if is_int(offset2label[offset]):
                inst.line_no = int(offset2label[offset])
                asm.code.co_lnotab[offset] = inst.line_no

        inst.offset = offset
        offset += xdis.op_size(inst.opcode, asm.opc)

        if xdis.op_has_argument(inst.opcode, asm.opc):
            if inst in backpatch:
                target = inst.arg
                match = re.match(r"^(L\d+)(?: \(to \d+\))?$", target)
                if match:
                    target = match.group(1)
                try:
                    if inst.opcode in asm.opc.JREL_OPS:
                        inst.arg = label[target] - offset
                    else:
                        inst.arg = label[target]
                        pass
                    pass
                except KeyError:
                    err(f"Label {target} not found.\nI know about {backpatch}", inst, i)
            elif is_int(inst.arg):
                if inst.opcode == asm.opc.EXTENDED_ARG:
                    extended_value += inst.arg
                    if asm.opc.version >= 3.6:
                        extended_value <<= 8
                    else:
                        extended_value <<= 16
                pass
            elif inst.arg.startswith("(") and inst.arg.endswith(")"):
                operand = inst.arg[1:-1]
                if inst.opcode in asm.opc.COMPARE_OPS:
                    if operand in cmp_op:
                        inst.arg = cmp_op.index(operand)
                    else:
                        err("Can't handle compare operand %s" % inst.arg, inst, i)

                    pass
                elif inst.opcode in asm.opc.CONST_OPS:
                    if not operand.startswith("<Code"):
                        operand = ast.literal_eval(operand)
                    update_code_field("co_consts", operand, inst, asm.code)
                elif inst.opcode in asm.opc.LOCAL_OPS:
                    update_code_field("co_varnames", operand, inst, asm.code)
                elif inst.opcode in asm.opc.NAME_OPS:
                    update_code_field("co_names", operand, inst, asm.code)
                elif inst.opcode in asm.opc.FREE_OPS:
                    if operand in asm.code.co_cellvars:
                        inst.arg = asm.code.co_cellvars.index(operand)
                    else:
                        update_code_field("co_freevars", operand, inst, asm.code)
                else:
                    # from trepan.api import debug; debug()
                    err("Can't handle operand %s" % inst.arg, inst, i)
            else:
                # from trepan.api import debug; debug()
                err(
                    "Don't understand operand %s expecting int or (..)" % inst.arg,
                    inst,
                    i,
                )

            if asm.opc.version_tuple < (3, 6):
                if inst.opcode == asm.opc.EXTENDED_ARG:
                    arg_tup = xdis.util.num2code(inst.arg)
                else:
                    arg_tup = xdis.util.num2code(inst.arg - extended_value)
                    extended_value = 0
                bcode += arg_tup
            # 3.6
            else:
                if inst.opcode == asm.opc.EXTENDED_ARG:
                    bcode.append(inst.arg)
                else:
                    bcode.append(inst.arg - extended_value)
                    extended_value = 0
        elif asm.opc.version_tuple >= (3, 6):
            bcode.append(0)

    if asm.opc.version_tuple >= (3, 0):
        co_code = bytearray()
        for j in bcode:
            co_code.append(j % 255)
        asm.code.co_code = bytes(co_code)
    else:
        asm.code.co_code = "".join([chr(j) for j in bcode])

    # Stamp might be added here
    if asm.python_version[:2] == PYTHON_VERSION_TRIPLE[:2]:
        code = asm.code.to_native()
    else:
        code = asm.code.freeze()
    # asm.print_instructions()

    # print (*args)
    # co = self.Code(*args)
    return code
