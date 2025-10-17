#!/usr/bin/env python
import ast
import re
from typing import Any, List, Optional

import xdis
from xdis import get_opcode, load_module
from xdis.opcodes.base import cmp_op
from xdis.version_info import PYTHON_VERSION_TRIPLE, version_str_to_tuple

# import xdis.bytecode as Mbytecode


class Instruction:  # (Mbytecode.Instruction):
    line_no: Optional[int]
    opname: str
    arg: Optional[int]

    def __repr__(self) -> str:
        if self.line_no:
            s = "%4d: " % self.line_no
        else:
            s = " " * 6
        s += f"{self.opname:15}"
        if self.arg is not None:
            s += f"\t{self.arg}"
        return s

    pass


def is_int(s: Any) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def match_lineno(s: str) -> Optional[re.Match]:
    return re.match(r"^\d+:", s)


def get_opname_operand(opc, fields: List[str]):
    assert len(fields) > 0
    opname = fields[0]
    if opc.opmap[opname] < opc.HAVE_ARGUMENT:
        return opname, None
    if len(fields) > 1:
        if is_int(fields[1]):
            operand = int(fields[1])
        else:
            operand = " ".join(fields[1:])
            if operand.startswith("(to "):
                int_val = operand[len("(to ") :]
                # In xasm format this shouldn't appear
                if is_int(int_val):
                    operand = int(int_val)

        return opname, operand
    else:
        return opname, None


class Assembler:
    def __init__(self, python_version, is_pypy) -> None:
        self.opc = get_opcode(python_version, is_pypy)
        self.code_list = []
        self.codes = []  # FIXME use a better name
        self.status: str = "unfinished"
        self.size = 0  # Size of source code. Only relevant in version 3 and above
        self.is_pypy = is_pypy
        self.python_version = python_version
        self.timestamp = None
        self.backpatch = []  # list of backpatch dicts, one for each function
        self.label = []  # list of label dists, one for each function
        self.code = None
        self.siphash = None

    def code_init(self, python_version=None) -> None:
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

    def update_lists(self, co, label, backpatch) -> None:
        self.code_list.append(co)
        self.codes.append(self.code)
        self.label.append(label)
        self.backpatch.append(backpatch)

    def print_instructions(self) -> None:
        for inst in self.code.instructions:
            if inst.line_no:
                print()
            print(inst)

    def warn(self, mess: str) -> None:
        """
        Print an error message and record that we warned, unless we have already errored.
        """
        print("Warning: ", mess)
        if self.status != "errored":
            self.status = "warning"

    def err(self, mess: str) -> None:
        """
        Print an error message and record that we errored.
        """
        print("Error: ", mess)
        self.status = "errored"


def asm_file(path) -> Optional[Assembler]:
    offset = 0
    methods = {}
    method_name = None
    asm = None
    backpatch_inst = set([])
    label = {}
    python_bytecode_version = None
    lines = open(path).readlines()
    i = 0
    bytecode_seen = False
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith("##"):
            # comment line
            continue
        if line.startswith(".READ"):
            match = re.match("^.READ (.+)$", line)
            if match:
                input_pyc = match.group(1)
                print(f"Reading {input_pyc}")
                (
                    version,
                    timestamp,
                    magic_int,
                    co,
                    is_pypy,
                    source_size,
                    sip_hash,
                ) = load_module(input_pyc)
                if python_bytecode_version and python_bytecode_version != version:
                    TypeError(
                        f"We previously saw Python version {python_bytecode_version} but we just loaded {version}.\n"
                    )
                python_bytecode_version = version
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

                python_bytecode_version = (
                    line[len("# Python bytecode " + pypy_str) :].strip().split()[0]
                )

                python_version_pair = version_str_to_tuple(
                    python_bytecode_version, length=2
                )
                asm = Assembler(python_version_pair, is_pypy)
                if python_version_pair >= (3, 10):
                    TypeError(
                        f"Creating Python version {python_bytecode_version} not supported yet. "
                        "Feel free to fix and put in a PR.\n"
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
                    co, is_valid = create_code(asm, label, backpatch_inst)
                    if not is_valid:
                        return
                    asm.update_lists(co, label, backpatch_inst)
                    label = {}
                    backpatch_inst = set([])
                    methods[method_name] = co
                    offset = 0
                if python_bytecode_version is None:
                    raise TypeError(
                        f'Line {i}: "Python bytecode" not seen before "Method Name:"; please set this.'
                    )
                python_version_pair = version_str_to_tuple(
                    python_bytecode_version, length=2
                )
                asm.code_init(python_version_pair)
                asm.code.co_qual_name = asm.code.co_name = line[
                    len("# Method Name: ") :
                ].strip()
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
                            f"Constant index {index} found on line {i} "
                            f"doesn't match expected constant index {count}."
                        )
                        expr = match.group(2)
                        match = re.match(
                            r"<(?:Code\d+ )?code object (\S+) at (0x[0-f]+)", expr
                        )
                        if match:
                            name = match.group(1)
                            m2 = re.match("^<(.+)>$", name)
                            if m2:
                                name = f"{m2.group(1)}_{match.group(2)}"
                            if name in methods:
                                asm.code.co_consts.append(methods[name])
                            else:
                                print(
                                    f"line {i} ({asm.code.co_filename}, {method_name}): can't find method {name}"
                                )
                                bogus_name = f"**bogus {name}**"
                                print(f"\t appending {bogus_name} to list of constants")
                                asm.code.co_consts.append(bogus_name)
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

            match = re.match(r"^(\S+):$", line)
            if match:
                label_value = match.group(1)
                # All-numeric labels, i.e. line numbers, are handled below
                if not re.match(r"^(\d+)$", label_value):
                    label[label_value] = offset
                    continue

            line_no = None

            match = re.match(r"^\s*(\d+):\s*", line)

            # Sanity checking: make sure we have seen
            # proper header lines
            if i == 1:
                assert bytecode_seen, (
                    f"Improper beginning:\n{line}"
                    "\nLine should begin with '#' "
                    "and contain header bytecode header information."
                )
            assert bytecode_seen, (
                f"Error translating line {i}: "
                "a line before this should include: \n"
                "# Python bytecode <version>"
            )

            if match:
                line_no = int(match.group(1))
                linetable_field = (
                    "co_lnotab" if python_version_pair < (3, 10) else "co_linetable"
                )
                assert asm is not None
                linetable = getattr(asm.code, linetable_field)
                linetable[offset] = line_no

            # Opcode section
            fields = line.strip().split()
            num_fields = len(fields)

            if num_fields == 1 and line_no is not None:
                continue

            try:
                if num_fields > 1:
                    if fields[0] == ">>":
                        fields = fields[1:]
                        num_fields -= 1
                    if match_lineno(fields[0]) and is_int(fields[1]):
                        line_no = int(fields[0][:-1])
                        opname, operand = get_opname_operand(asm.opc, fields[2:])
                    elif match_lineno(fields[0]):
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
            except Exception as e:
                print(f"Line {i}: {e}")
                raise

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
                raise RuntimeError(f"Illegal opname {opname} in:\n{line}")
            pass
        pass

    if asm is not None:
        # print(linetable)

        co, is_valid = create_code(asm, label, backpatch_inst)
        asm.update_lists(co, label, backpatch_inst)
        asm.code_list.reverse()
        asm.status = "finished"

    return asm


def member(fields, match_value) -> int:
    for i, v in enumerate(fields):
        if v == match_value and type(v) == type(match_value):
            return i
        pass
    return -1


def update_code_field(field_name: str, value, inst, opc) -> None:
    field_values = getattr(opc, field_name)
    # Can't use "in" because True == 1 and False == 0
    # if value in l:
    i = member(field_values, value)
    if i >= 0:
        inst.arg = i
    else:
        inst.arg = len(field_values)
        field_values.append(value)


def update_code_tuple_field(field_name: str, code, lines: List[str], i: int):
    count = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        match = re.match(r"^#\s+(\d+): (.+)$", line)
        if match:
            index = int(match.group(1))
            assert (
                index == count
            ), f'In field" "{field_name}", line {i}, number {index} is expected to have value {count}.'
            field_values = getattr(code, field_name)
            field_values.append(match.group(2))
            count += 1
        else:
            i -= 1
            break
        pass
    return i


def err(msg: str, inst, i: int):
    msg += ". Instruction %d:\n%s" % (i, inst)
    raise RuntimeError(msg)


def warn(mess: str) -> None:
    """
    Print an error message and record that we warned.
    """
    print("Warning: ", mess)


def decode_lineno_tab_old(lnotab, first_lineno: int) -> dict:
    """
    Uncompresses line number table for Python versions before
    3.10
    """
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
        uncompressed_lnotab[offset] = line_number

    return uncompressed_lnotab


def is_code_ok(asm: Assembler) -> bool:
    """
    Performs some sanity checks on code.
    """

    is_valid: bool = True

    code = asm.code
    last_instruction = code.instructions[-1]
    last_offset = last_instruction.offset
    if last_instruction.opname not in ("RETURN_VALUE", "RERAISE", "RAISE_VARARGS"):
        warn(
            f"Last instruction of at offset {last_offset} of {code.co_name}"
            f' should be "RETURN_VALUE", is "{last_instruction.opname}"'
        )
        is_valid = False

    cells_free_len = len(code.co_freevars) + len(code.co_cellvars)
    consts_len = len(code.co_consts)
    names_len = len(code.co_names)
    varnames_len = len(code.co_varnames)

    for i, inst in enumerate(code.instructions):
        if xdis.op_has_argument(inst.opcode, asm.opc):
            if is_int(inst.arg):
                if inst.opcode == asm.opc.EXTENDED_ARG:
                    continue
                operand = inst.arg
                if inst.opcode in asm.opc.CONST_OPS:
                    # FIXME: DRY operand check
                    if operand >= consts_len:
                        print(inst)
                        warn(
                            f"Constant operand index {operand} at offset {inst.offset} of {code.co_name} "
                            f"is too large; it should be less than {consts_len}."
                        )
                        is_valid = False
                elif inst.opcode in asm.opc.LOCAL_OPS:
                    if operand >= varnames_len:
                        print(inst)
                        warn(
                            f"Variable operand index {operand} at offset {inst.offset} of {code.co_name} "
                            f"is too large; it should be less than {varnames_len}."
                        )
                        is_valid = False
                elif inst.opcode in asm.opc.NAME_OPS:
                    if operand >= names_len:
                        print(inst)
                        warn(
                            f"Name operand index {operand} at offset {inst.offset} of {code.co_name} "
                            f"is too large; it should be less than {names_len}."
                        )
                        is_valid = False
                elif inst.opcode in asm.opc.FREE_OPS:
                    # FIXME: is this right?
                    if operand >= cells_free_len:
                        print(inst)
                        warn(
                            f"Free operand index {operand} at offset {inst.offset} of {code.co_name} "
                            f"is too large; it should be less than {cells_free_len}."
                        )
                        is_valid = False

    return is_valid


def append_operand(
    bytecode: list, arg_value, extended_arg_shift, arg_max_value, extended_arg_op
) -> None:
    """
    Write instruction operand adding EXTENDED_ARG instructions
    when necessary.
    """
    arg_shifts = []
    shift_value = 1

    while arg_value > arg_max_value:
        shift_value <<= extended_arg_shift
        ext_arg_value, arg_value = divmod(arg_value, shift_value)
        arg_shifts.append(ext_arg_value)

    while arg_shifts:
        bytecode.append(extended_arg_op)
        ext_arg_value = arg_shifts.pop()
        bytecode.append(ext_arg_value)

    bytecode.append(arg_value)


def create_code(asm: Assembler, label, backpatch) -> tuple:
    """
    Turn ``asm`` assembler text into a code object and
    return that.
    """
    # print('label: ', asm.label)
    # print('backpatch: ', asm.backpatch_inst)

    bytecode = []
    # print(asm.code.instructions)

    offset = 0
    offset2label = {label[j]: j for j in label}
    is_valid = True

    for i, inst in enumerate(asm.code.instructions):
        # Strip out extended arg instructions.
        # Operands in the input can be arbitary numbers.
        # In this loop we will figure out whether
        # or not to add EXTENDED_ARG
        if inst.opcode == asm.opc.EXTENDED_ARG:
            print(
                f"Line {i}: superflous EXTENDED_ARG instruction removed;"
                " this code decides when they are needed."
            )
            continue

        bytecode.append(inst.opcode)
        if offset in offset2label:
            if is_int(offset2label[offset]):
                inst.line_no = int(offset2label[offset])
                if (
                    inst.line_no in asm.code.co_lnotab.values()
                    and asm.python_version < (3, 10)
                ):
                    print(
                        f"Line {i}: this is not the first we encounter source-code line {inst.line_no}."
                    )
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
                    if asm.opc.version_tuple >= (3, 10):
                        inst.arg >>= 1
                    pass
                except KeyError:
                    err(f"Label {target} not found.\nI know about {backpatch}", inst, i)
                    is_valid = False
            elif is_int(inst.arg):
                pass
            elif inst.arg.startswith("(") and inst.arg.endswith(")"):
                operand = inst.arg[1:-1]
                if inst.opcode in asm.opc.COMPARE_OPS:
                    if operand in cmp_op:
                        inst.arg = cmp_op.index(operand)
                    else:
                        err(f"Can't handle compare operand {inst.arg}", inst, i)
                        is_valid = False
                        break

                    pass
                elif inst.opcode in asm.opc.CONST_OPS:
                    if not (operand.startswith("<Code") or operand.startswith("<code")):
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
                    err(f"Can't handle operand {inst.arg}", inst, i)
                    is_valid = False
                    break
            else:
                # from trepan.api import debug; debug()
                err(
                    f"Don't understand operand {inst.arg} expecting int or (..)",
                    inst,
                    i,
                )

            append_operand(
                bytecode,
                inst.arg,
                asm.opc.EXTENDED_ARG_SHIFT,
                asm.opc.ARG_MAX_VALUE,
                asm.opc.EXTENDED_ARG,
            )

        elif asm.opc.version_tuple >= (3, 6):
            # instructions with no operand, or one-byte instructions, are padded
            # to two bytes in 3.6 and later.
            bytecode.append(0)

    if not is_valid:
        return None, False

    if asm.opc.version_tuple >= (3, 0):
        co_code = bytearray()
        for j in bytecode:
            co_code.append(j % 255)
        asm.code.co_code = bytes(co_code)
    else:
        asm.code.co_code = "".join([chr(j) for j in bytecode])

    # FIXME: get
    is_code_ok(asm)

    # Stamp might be added here
    if asm.python_version[:2] == PYTHON_VERSION_TRIPLE[:2]:
        code = asm.code.to_native()
    else:
        code = asm.code.freeze()

    # asm.print_instructions()

    # print (*args)
    # co = self.Code(*args)
    return code, is_valid
