xasm
====

*NOTE: this is in an early beta stage*

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

This will support bytecodes from Python version 1.5 to 3.6 or so.

The code requires Python 2.7 or later.

Assembly files
--------------

More detail will be filled in, but some principles:

* Preferred extension for Python assembly is `.pyasm`
* assembly is designed to work with the output of `pydisasm`
* Assembly file labels are at the beginning of the line
  and end in a colon, e.g. 'END_IF:'
* instruction offsets in the assembly file are ignored and don't need
  to be entered
* in those instructions that refer to offsets, if the if the
  operand is an int, exactly that value will be used for the operand. Otherwise
  we will look for labels and match up with that


Installation
------------

This uses setup.py, so it follows the standard Python routine:

::

    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    python setup.py install # may need sudo
    # or if you have pyenv:
    python setup.py develop

A GNU makefile is also provided so :code:`make install` (possibly as root or
sudo) will do the steps above.

Usage
-----

Run

::

     pyxasm  <Python assembler file>


For usage help  `pyxasm --help`



See Also
--------
* https://github.com/rocky/python-xdis : Cross Python version disassemble
* https://github.com/rocky/python-xasm/blob/master/HOW-TO-USE.rst : How to write an assembler file

.. _uncompyle6: https://github.com/rocky/python-uncompyle6
