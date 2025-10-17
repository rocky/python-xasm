#!/usr/bin/env python
import os
import sys
from typing import List

import click
import xdis
from xdis.version_info import version_tuple_to_str

from xasm.assemble import asm_file
from xasm.write_pyc import write_pycfile


@click.command()
@click.option("--pyc-file", default=None)
@click.argument("asm-path", type=click.Path(exists=True, readable=True), required=True)
def main(pyc_file: List[str], asm_path):
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
        print(f"Size of assembly file {asm_path} is zero")
        sys.exit(1)
    asm = asm_file(asm_path)

    if not pyc_file:
        if asm_path.endswith(".pyasm"):
            pyc_file = asm_path[: -len(".pyasm")] + ".pyc"
        elif not pyc_file and asm_path.endswith(".xasm"):
            pyc_file = asm_path[: -len(".xasm")] + ".pyc"

    if xdis.PYTHON3:
        file_mode = "wb"
    else:
        file_mode = "w"

    with open(pyc_file, file_mode) as fp:
        rc = write_pycfile(
            fp, asm.code_list, asm.timestamp, asm.python_version, asm.is_pypy
        )
        size = fp.tell()
    print(
        f"""Wrote Python {version_tuple_to_str(asm.python_version)} bytecode file "{pyc_file}"; {size} bytes."""
    )
    if size <= 16:
        print("Warning: bytecode file is too small to be usable.")
        rc = 2
    if rc != 0:
        print(f"Exiting with return code {rc}")
    sys.exit(rc)


if __name__ == "__main__":
    main(sys.argv[1:])
