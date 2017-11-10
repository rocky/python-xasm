#!/usr/bin/env python
import click, os, py_compile, sys

@click.command()
@click.option('--compile/--no-compile', default=None)
@click.option('--disasm/--no-disasm', default=True)
@click.option('--asm/--no-asm', default=None)
@click.argument('files', nargs=-1, type=click.Path(exists=True, readable=True), required=True)
def main(compile, disasm, asm, files):
    """
    Byte-compile, get assembly listing, assemble, and run a Python program
    """

    # We do this crazy way to support Python 2.6 which
    # doesn't support version_major, and has a bug in
    # floating point so we can't divide 26 by 10 and get
    # 2.6
    PY_VERSION = sys.version_info[0] + (sys.version_info[1] / 10.0)

    for path in files:

        if compile is None:
            do_compile = path.endswith('.py')
        else:
            do_compile = compile and disasm

        if do_compile:
            if asm is None:
                asm = True
            if path.endswith('.py'):
                basename = path[:-len('.py')]
            else:
                basename = path

            ver_prefix = "%s-%s" % (basename, PY_VERSION)
            bytecode = "%s-good.pyc" % (ver_prefix)
            produced_bytecode = "%s.pyc" % (ver_prefix)
            print("compiling %s to %s" % (path, bytecode))
            py_compile.compile(path, bytecode)
        else:
            bytecode = path

        have_disasm_path = path.endswith('.pyc') or path.endswith('.pyo')
        have_asm_path = path.endswith('.pyasm')
        if disasm is None:
            do_disasm = have_disasm_path
        else:
            do_disasm = disasm and not have_asm_path
            if disasm and asm is None:
                asm = True

        if do_disasm:
            if have_disasm_path:
                produced_bytecode = path
                bytecode = path
                basename = path[:-len('.pyo')]
                asm_file = "%s.pyasm" % basename
            else:
                asm_file = "%s.pyasm" % ver_prefix

            cmd = "pydisasm --asm %s > %s" % (bytecode, asm_file)
            print(cmd)
            os.system(cmd)

        if have_asm_path:
            basename = path[:-len('.pyasm')]
            ver_prefix = basename
            asm_file = path
            produced_bytecode = "%s.pyc" % ver_prefix

        if asm is None:
            do_asm = have_asm_path
        else:
            do_asm = asm

        if do_asm:
            cmd = "../xasm/xasm_cli.py %s" % asm_file
            print(cmd)
            os.system(cmd)
            cmd = "%s %s" % (sys.executable, produced_bytecode)
            print(cmd)
            os.system(cmd)

if __name__ == '__main__':
    main(sys.argv[1:])
