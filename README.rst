pyxasm
==========

*NOTE: this is in an early beta stage*

A Cross-Python bytecode Assembler


Introduction
------------

The Python `xasm` module has routines for assembly, and has a command to
assemble bytecode for several different versions of Python.

Here are some potential uses:

* Write more efficient bytecode
* Write an instruction-level optimizing compiler
* Experiment and learn about Python Bytecode
* Foil uncompyle6_ in being able to disassemble you bytecode

This will support bytecodes from Python version 1.5 to 3.6 or so.
Currently though only 2.6, 2.7 and 3.4 are planned.

The code requires Python 2.7 or later.

Assembly files
--------------

More detail will be filled in, but some principles:

* Prefered extension for Python assembly is `.pyasm`
* assembly is designed to work with the output of `pydisasm`
* Assesembly file lables are at the beginning of the line
  and end in a colon, e.g. 'END_IF:'
* instruction offsets in the assembly file are ignored and don't need
  to be enteed
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

Testing
-------

::

   make check

A GNU makefile has been added to smooth over setting running the right
command, and running tests from fastest to slowest.

If you have remake_ installed, you can see the list of all tasks
including tests via :code:`remake --tasks`.


Usage
-----

Run

::

     pyxasm  --asm-file <Python assembler file>


For usage help  `pyxasm --help`



See Also
--------
* https://github.com/rocky/python-xdis : Cross Python version dissasemble

.. _uncompyle6: https://github.com/rocky/python-uncompyle6
.. _remake: http://bashdb.sf.net/remake

