|Pypi Installs| |Latest Version| |Supported Python Versions|

xasm
====

*NOTE: this is in beta*

A Cross-Python bytecode Assembler


Introduction
------------

The Python `xasm` module has routines for assembly, and has a command to
assemble bytecode for several different versions of Python.

Here are some potential uses:

* Make small patches to existing Python bytecode when you don’t have source
* Craft custom and efficient bytecode
* Write an instruction-level optimizing compiler
* Experiment with and learn about Python bytecode
* Foil uncompyle6_ so that it can’t disassemble bytecode (at least for now)

This will support bytecodes from Python version 1.0 to 3.8 or so.

The code requires Python 2.7 or later.

Assembly files
--------------

More detail will be filled in, but some principles:

* Preferred extension for Python assembly is `.pyasm`
* assembly is designed to work with the output of `pydisasm --asm`
* Assembly file labels are at the beginning of the line
  and end in a colon, e.g. `END_IF`
* instruction offsets in the assembly file are ignored and don't need
  to be entered
* in those instructions that refer to offsets, if the if the
  operand is an int, exactly that value will be used for the operand. Otherwise
  we will look for labels and match up with that


Installation
------------

The standard Python routine:

::

    pip install -e .
    pip install -r requirements-dev.txt

A GNU makefile is also provided so :code:`make install` (possibly as root or
sudo) will do the steps above.


Testing
-------

::

   make check

A GNU makefile has been added to smooth over setting running the right
command, and running tests from fastest to slowest.

If you have remake_ installed, you can see the list of all tasks
including tests via :code:`remake --tasks`.


Example Assembly File
---------------------

For this Python source code:

::

    def five():
        return 5

    print(five())

Here is an assembly for the above:

::

    # Python bytecode 3.6 (3379)

    # Method Name:       five
    # Filename:          /tmp/five.pl
    # Argument count:    0
    # Kw-only arguments: 0
    # Number of locals:  0
    # Stack size:        1
    # Flags:             0x00000043 (NOFREE | NEWLOCALS | OPTIMIZED)
    # First Line:        1
    # Constants:
    #    0: None
    #    1: 5
      2:
                LOAD_CONST           (5)
                RETURN_VALUE


    # Method Name:       <module>
    # Filename:          /tmp/five.pl
    # Argument count:    0
    # Kw-only arguments: 0
    # Number of locals:  0
    # Stack size:        2
    # Flags:             0x00000040 (NOFREE)
    # First Line:        1
    # Constants:
    #    0: <code object five at 0x0000>
    #    1: 'five'
    #    2: None
    # Names:
    #    0: five
    #    1: print
      1:
                LOAD_CONST           0 (<code object five at 0x0000>)
                LOAD_CONST           ('five')
                MAKE_FUNCTION        0
                STORE_NAME           (five)

      3:
                LOAD_NAME            (print)
                LOAD_NAME            (five)
                CALL_FUNCTION        0
                CALL_FUNCTION        1
                POP_TOP
                LOAD_CONST           (None)
                RETURN_VALUE


The above can be created automatically from Python source code using the `pydisasm`
command from `xdis`:

::

    pydisasm --asm /tmp/five.pyc

In the example above though, I have shortend and simplified the result.


Usage
-----

To create a python bytecode file from an assemble file, run:

::

   pyc-xasm [OPTIONS] ASM_PATH


For usage help, type  `pyc-xasm --help`.


To convert a python bytecode from one bytecode to another, run:

::

   pyc-convert [OPTIONS] INPUT_PYC [OUTPUT_PYC]


For usage help, type  `pyc-convert --help`.


See Also
--------

* https://github.com/rocky/python-xdis : Cross Python version disassemble
* https://github.com/rocky/x-python : Cross Python version interpreter
* https://github.com/rocky/python-xasm/blob/master/HOW-TO-USE.rst : How to write an assembler file
* https://rocky.github.io/pycon2018-light.co/ : Pycolumbia 2018 Lightning talk showing how to use the assembler


.. _uncompyle6: https://github.com/rocky/python-uncompyle6
.. |Latest Version| image:: https://badge.fury.io/py/xasm.svg
		 :target: https://badge.fury.io/py/xasm
.. |Pypi Installs| image:: https://pepy.tech/badge/xasm
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/xasm.svg
.. _remake: http://bashdb.sf.net/remake
