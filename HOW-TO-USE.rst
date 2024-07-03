Introduction
============

Welcome back to the wonderful times world of SEGV's (from the Python interpreter)!

If you mess up on the bytecode you may get a SEGV with no further information.

Although it is possible to write assembler code from scratch, for now
it's much easier to start off using Python code, even if
skeletal. Then use ``pydisasm --xasm`` to convert to the Python source
code assembler format. From this then modify the results and run
``pyc-xasm``.

In normal Python disassembly code (and in the bytecode file), the main
function appears first; it contains constants which contain code to
other functions and so on. In Python disassembly these are linearized
so that from top down you have a topological sort of the dependencies.

However in the assembler file input to ``pyxasm``, it has to come the
other way: The assembler for the main code has to come last: after all
of the things it calls are listed beforehand. This is necessary
because as the assembler reads the assembly file and builds code
objects as it goes along. So the first routines have to be those that
don't call any others (aside possibly itself recursively).

And while on the topic, let me mention something about function
calls. Right now, that I guess is kind of a pain because you need to
must use the funky encoding Python uses in its CALL_FUNCTION
instructions. Another reason why using ``pydisasm --xasm`` is
preferable right now.

Format of assembly file
=======================

Again, easiest to consult the ``pydisasm --xasm`` output ``.pyasm``-file that is
produced. Even easier, just to look in the test directory_ for files that end
with ``.pyasm``.

Lines that start with '##" are comments.

Examples::

    ## This line is a comment
    ## Method Name:       GameSheet

Lines that start with ``#``" in column one are used to indicate a code
or function object that is not a bytecode instructions. However this
is only true if the rest of the line matches one of the code of
function objects mentioned below. If instead the the rest of a line
does not match a function or code object, it line too will be
treated tacitly as a comment.

Module-level info
------------------


The only necessary mdoule-level inforamation that is needed is the
Python "magic" number which determines which Python bytecode opcodes
to use and which Python interpreter can be used to run the resulting
program.

Optional information includes:

* Timestamp of code
* Source code size module 2**32 or a SIP hash

Here is an example of the module-level information:

::

   # Python bytecode 2.2 (60717)
   # Timestamp in code: 1499156389 (2017-07-04 04:19:49)
   # Source code size mod 2**32: 577 bytes

Again, the bytecode number is necessary. However the timestamp is not. In Python 3
there is also a size modulo 2**32 that is recorded, and in later Python this can be a
SIP hash.

::


Method-level info
------------------

Method-level information starts with ``#`` in column one. Here is some
method-level information:

* The method name of the code object (``Method Name``)
* Number of local variables used in module or function (``Number of locals``)
* A filename where the file (``Filename``)
* Maximum Stack Size needed to run code (``Stack Size``)
* Code flags which indicate properties of the code (``Flags``)
* Fine number for the first line of the code (``First Line``)

Here is an example:

::

   # Method Name: gcd
   # Filename: exec
   # Argument count: 2
   # Kw-only arguments: 0
   # Number of locals: 2
   # Stack size: 3
   # Flags: 0x00000043 (NOFREE | NEWLOCALS | OPTIMIZED)
   # First Line: 11
   # Constants:
   # 0: ' GCD. We assume positive numbers'
   # 1: 0
   # 2: None
   # 3: 1
   # Names:
   # 0: gcd
   # Varnames:
   # a, b
   # Positional arguments:
   # a, b
   # Local variables:
   # 1: i
   # Free variables:
   # 0: o
   # Cell variables:
   # 0: i

Some of these can be omitted and default values will be used. For the
lists like Constants, Names, and so on, those can be omitted too. But
if they are, the instruction section can't refer to those values by list index value. (List index value is however used in the actual bytecode.)

Although we haven't gotten to the exact format of instructions, what
the last sentence means is that

::

   LOAD_CONST 3

would be invalid if the size of the constant array is less than 4, or `constant[3]` wasn't defined by adding it to the `Constants` section. However when you put a value in parenthesis, that indicate a value rather than an index into a list.
So you could instead write:

::

   LOAD_CONST (1)

which in this case does the same thing since `1 = constant[3]`. If the value 1 does not appear anywhere in the constants list, the assembler would append the value 1 to the end of the list of the constants list. When writing the final bytecode file an appropriate constant index will be inserted into that instruction.

Line Numbers and Labels
-----------------------

If the first token on a line is a number followed with a colon it is
taken as a line number to be applied to the next instruction. For
example

::

   66:
       LOAD_CONST ('this is line 66')

The ``LOAD_CONST`` instruction will be noted as being on line 66. Note
that Python before version 3.10 requires that line numbers don't decrease as the a
method increases in bytecode offset. Also note that there can be white
space before the line number; the number doesn't have to be in
column 1.

Labels are like line numbers in that they have a colon suffix on the
line and must be the first thing on a line. However The first
character of a label *cannot* be a number: that's how we distinguish
between line numbers and labels. Here is a label:

::

   L33:
       POP_TOP

Inside an instruction you refer to the label without the trialing colon. For example:

::

    POP_JUMP_IF_TRUE L33 (to 33)

Instructions
-------------

The module level bytecode line determines what Python opcodes are
acceptable and how operands are interpreted.

Instructions come after the other module or function information that starts with `#` and
is shown above.

An instruction then is something that is not a comment or code or
module field which would start with a #. And it is not a line number
or label listed in the last section. We've seen examples of
instructions above.

Operation name
...............

Instructions start with an opcode name like ``LOAD_CONST``. The specific opcode names used depends on the Python version you are using.
So make sure to consult the "opcodes" section of the "dis" module documentation for the version of Python listed at the top of the metadata section.


Operand
........


An instruction may also have an operand depending
on whether the opcode requires one or not. However as we've seen above,
the operands can take a couple of forms. The operand can be a number
which represents a bytecode offset, or an index into one of the method
lists like the Constants, or Names list. I don't recommend though that
you use this form. Instead use labels where instead of offsets and
list the values for list rather than an index.

And operands other than offsets or labels, should be enclosed in
parenthesis. For example:

::

    LOAD_CONST (3)    # loads number 3
    LOAD_CONST 3      # load Constants[3]
    JUMP_ABSOLUTE 10  # Jumps to offset 10
    JUMP_ABSOLUTE L10 # Jumps to label L10
    LOAD_CONSTANT (('load_entry_point',)) # Same as: tuple('load_entry_point')

Instructions can also have additional stuff after the operand and that is ignored.

Internally operand values are integers or indexes in some table. When an index value is more than 255 (the largest value that fits in a single byte), an ``EXTENDED_OPERAND`` instruction is added automatically.

Cool Stuff
----------

Just that this even works blows my mind.

First of all the fact that we can output bytecode for different
versions is pretty neat. Even more, the bytecode version you produce
doesn't have to be the same as the Python interpreter that runs
``pyc-xasm``. That's why there's that "x": it stands for
"cross"

TODO
-----

We should have a better API to generate instructions from inside
Python. This is pretty straightforward to do.

There is some error checking of consistency of the input file, but more  error checking is desirable.

.. _directory: https://github.com/rocky/python-xasm/tree/master/test
