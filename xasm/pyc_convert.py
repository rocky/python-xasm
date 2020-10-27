#!/usr/bin/env python
"""Convert Python Bytecode from one version to another for
some limited set of Python bytecode versions
"""
from xdis import disassemble_file, load_module, magic2int, write_bytecode_file
from xasm.write_pyc import write_pycfile
import xdis
from xdis.opcodes import opcode_33, opcode_27
from tempfile import NamedTemporaryFile
import os.path as osp
import os
from copy import copy
from xasm.assemble import (
    asm_file,
    Assembler,
    create_code,
    Instruction,
    decode_lineno_tab,
)
from xdis.magics import magics
import click

from xasm.version import __version__


def add_credit(asm, src_version, dest_version):
    stamp = "Converted from Python %s to %s by %s version %s" % (
        src_version,
        dest_version,
        "pyc-convert",
        __version__,
    )
    asm.codes[-1].co_consts = list(asm.codes[-1].co_consts).append(stamp)
    return


def copy_magic_into_pyc(input_pyc, output_pyc, src_version, dest_version):
    """Bytecodes are the same except the magic number, so just change
    that"""
    (version, timestamp, magic_int, co, is_pypy, source_size) = load_module(input_pyc)
    assert version == float(
        src_version
    ), "Need Python %s bytecode; got bytecode for version %s" % (src_version, version)
    magic_int = magic2int(magics.magics[dest_version])
    write_bytecode_file(output_pyc, co, magic_int)
    print("Wrote %s" % output_pyc)
    return


def xlate26_27(inst):
    """Between 2.6 and 2.7 opcode values changed
    Adjust for the differences by using the opcode name
    """
    inst.opcode = opcode_27.opmap[inst.opname]


def conversion_to_version(conversion_type, is_dest=False):
    if is_dest:
        return conversion_type[-2] + "." + conversion_type[-1]
    else:
        return conversion_type[0] + "." + conversion_type[1]


def transform_26_27(inst, new_inst, i, n, offset, instructions, new_asm):
    """Change JUMP_IF_FALSE and JUMP_IF_TRUE to
    POP_JUMP_IF_FALSE and POP_JUMP_IF_TRUE"""
    if inst.opname in ("JUMP_IF_FALSE", "JUMP_IF_TRUE"):
        i += 1
        assert i < n
        assert instructions[i].opname == "POP_TOP"
        new_inst.offset = offset
        new_inst.opname = (
            "POP_JUMP_IF_FALSE"
            if inst.opname == "JUMP_IF_FALSE"
            else "POP_JUMP_IF_TRUE"
        )
        new_asm.backpatch[-1].remove(inst)
        new_inst.arg = "L%d" % (inst.offset + inst.arg + 3)
        new_asm.backpatch[-1].add(new_inst)
    else:
        xlate26_27(new_inst)
    return xdis.op_size(new_inst.opcode, opcode_27)


def transform_32_33(inst, new_inst, i, n, offset, instructions, new_asm):
    """MAKE_FUNCTION adds another const. probably MAKE_CLASS as well
    """
    add_size = xdis.op_size(new_inst.opcode, opcode_33)
    if inst.opname in ("MAKE_FUNCTION", "MAKE_CLOSURE"):
        # Previous instruction should be a load const which
        # contains the name of the function to call
        prev_inst = instructions[i - 1]
        assert prev_inst.opname == "LOAD_CONST"
        assert isinstance(prev_inst.arg, int)

        # Add the function name as an additional LOAD_CONST
        load_fn_const = Instruction()
        load_fn_const.opname = "LOAD_CONST"
        load_fn_const.opcode = opcode_33.opmap["LOAD_CONST"]
        load_fn_const.line_no = None
        prev_const = new_asm.code.co_consts[prev_inst.arg]
        if hasattr(prev_const, "co_name"):
            fn_name = new_asm.code.co_consts[prev_inst.arg].co_name
        else:
            fn_name = "what-is-up"
        const_index = len(new_asm.code.co_consts)
        new_asm.code.co_consts = list(new_asm.code.co_consts)
        new_asm.code.co_consts.append(fn_name)
        load_fn_const.arg = const_index
        load_fn_const.offset = offset
        load_fn_const.starts_line = False
        load_fn_const.is_jump_target = False
        new_asm.code.instructions.append(load_fn_const)
        load_const_size = xdis.op_size(load_fn_const.opcode, opcode_33)
        add_size += load_const_size
        new_inst.offset = offset + add_size
        pass
    return add_size


def transform_33_32(inst, new_inst, i, n, offset, instructions, new_asm):
    """MAKE_FUNCTION, and MAKE_CLOSURE have an additional LOAD_CONST of a name
    that are not in Python 3.2. Remove these.
    """
    add_size = xdis.op_size(new_inst.opcode, opcode_33)
    if inst.opname in ("MAKE_FUNCTION", "MAKE_CLOSURE"):
        # Previous instruction should be a load const which
        # contains the name of the function to call
        prev_inst = instructions[i - 1]
        assert prev_inst.opname == "LOAD_CONST"
        assert isinstance(prev_inst.arg, int)
        assert len(instructions) > 2
        assert len(instructions) > 2
        prev_inst2 = instructions[i - 2]
        assert prev_inst2.opname == "LOAD_CONST"
        assert isinstance(prev_inst2.arg, int)

        # Remove the function name as an additional LOAD_CONST
        prev2_const = new_asm.code.co_consts[prev_inst.arg]
        assert hasattr(prev2_const, "co_name")
        new_asm.code.instructions = new_asm.code.instructions[:-1]
        load_const_size = xdis.op_size(prev_inst.opcode, opcode_33)
        add_size -= load_const_size
        new_inst.offset = offset - add_size
        return -load_const_size
    return 0


def transform_asm(asm, conversion_type, src_version, dest_version):

    new_asm = Assembler(dest_version)
    for field in "code size".split():
        setattr(new_asm, field, copy(getattr(asm, field)))

    if conversion_type == "26-27":
        transform_fn = transform_26_27
    elif conversion_type == "32-33":
        transform_fn = transform_32_33
    elif conversion_type == "33-32":
        transform_fn = transform_33_32
    else:
        raise RuntimeError("Don't know how to covert %s " % conversion_type)
    for j, code in enumerate(asm.code_list):
        offset2label = {v: k for k, v in asm.label[j].items()}
        new_asm.backpatch.append(copy(asm.backpatch[j]))
        new_asm.label.append(copy(asm.label[j]))
        new_asm.codes.append(copy(code))
        new_asm.code.co_lnotab = decode_lineno_tab(code.co_lnotab, code.co_firstlineno)
        instructions = asm.codes[j].instructions
        new_asm.code.instructions = []
        i, offset, n = 0, 0, len(instructions)
        while i < n:
            inst = instructions[i]
            new_inst = copy(inst)
            inst_size = transform_fn(
                inst, new_inst, i, offset, n, instructions, new_asm
            )
            if inst.offset in offset2label:
                new_asm.label[-1][offset2label[inst.offset]] = offset
                pass
            offset += inst_size
            new_asm.code.instructions.append(new_inst)
            i += 1
            pass

    co = create_code(new_asm, new_asm.label[-1], new_asm.backpatch[-1])
    new_asm.code_list.append(co)
    new_asm.code_list.reverse()
    new_asm.finished = "finished"
    return new_asm


UPWARD_COMPATABLE = tuple("20-21 21-22 23-24 24-23".split())


@click.command()
@click.option(
    "--conversion-type",
    "-t",
    type=click.Choice(
        [
            "20-21",
            "21-22",
            "23-24",
            "24-23",
            "24-25",
            "25-26",
            "26-27",
            "32-33",
            "33-32",
        ]
    ),
    help="specify conversion from/to bytecode",
    default="26-27",
)
@click.argument("input_pyc", type=click.Path("r"), nargs=1)
@click.argument(
    "output_pyc", type=click.Path("w"), required=False, nargs=1, default=None
)
def main(conversion_type, input_pyc, output_pyc):
    """Convert Python bytecode from one version to another.

    INPUT_PYC contains the input bytecode path name
    OUTPUT_PYC  contians the output bytecode path name if supplied
    The --conversion type option specifies what conversion to do.

    Note: there are a very limited set of conversions currently supported.
    Help out and write more!"""

    shortname = osp.basename(input_pyc)
    if shortname.endswith(".pyc"):
        shortname = shortname[:-4]
    src_version = conversion_to_version(conversion_type, is_dest=False)
    dest_version = conversion_to_version(conversion_type, is_dest=True)
    if output_pyc is None:
        output_pyc = "%s-%s.pyc" % (shortname, dest_version)

    if conversion_type in UPWARD_COMPATABLE:
        copy_magic_into_pyc(input_pyc, output_pyc, src_version, dest_version)
        return
    temp_asm = NamedTemporaryFile("w", suffix=".pyasm", prefix=shortname, delete=False)
    (filename, co, version, timestamp, magic_int) = disassemble_file(
        input_pyc, temp_asm, asm_format=True
    )
    temp_asm.close()
    assert version == float(
        src_version
    ), "Need Python %s bytecode; got bytecode for version %s" % (src_version, version)
    asm = asm_file(temp_asm.name)
    new_asm = transform_asm(asm, conversion_type, src_version, dest_version)
    os.unlink(temp_asm.name)
    write_pycfile(output_pyc, new_asm)


if __name__ == "__main__":
    main()
