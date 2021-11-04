#!/usr/bin/env python
import click, os, sys
from xasm.assemble import asm_file
from xasm.write_pyc import write_pycfile
import xdis
from xdis.version_info import version_tuple_to_str


@click.command()
@click.option("--pyc-file", default=None)
@click.argument("asm-path", type=click.Path(exists=True, readable=True), required=True)
def main(pyc_file, asm_path):
    """
    Create Python bytecode from a Python assembly file.

    ASM_PATH gives the input Python assembly file. We suggest ending the
    file in .pyc

    If --pyc-file is given, that indicates the path to write the
    Python bytecode. The path should end in '.pyc'.

    See https://github.com/rocky/python-xasm/blob/master/HOW-TO-USE.rst
    for how to write a Python assembler file.
    """
    if os.stat(asm_path).st_size == 0:
        print("Size of assembly file %s is zero" % asm_path)
        sys.exit(1)
    asm = asm_file(asm_path)

    if not pyc_file and asm_path.endswith(".pyasm"):
        pyc_file = asm_path[: -len(".pyasm")] + ".pyc"

    if xdis.PYTHON3:
        file_mode = "wb"
    else:
        file_mode = "w"

    with open(pyc_file, file_mode) as fp:
        write_pycfile(fp, asm.code_list, asm.timestamp, asm.python_version)
        size = fp.tell()
    print(
        f"""Wrote Python {version_tuple_to_str(asm.python_version)} bytecode file "{pyc_file}"; {size} bytes."""
    )
    if size <= 16:
        print("Warning: bytecode file is too small to be usuable.")


if __name__ == "__main__":
    main(sys.argv[1:])
