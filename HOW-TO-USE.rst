Introduction
*************

Welcome back to the wonderful times world of SEGV's (from the Python interpreter)!

If you mess up on the bytecode you may get a SEGV with no further information.

Although it is possible to write assembler code from scratch, for now
it's much easier to start off using Python code, even if
skeletal. Then use ``pydisasm --xasm`` to convert to the Python source
code assembler format. From this then modify the results and run
``pyc-xasm``.

In normal python disassembly code (and in the bytecode file), the main
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
-----------------------

Again, easiest to consult the ``pydiasm --xasm`` output ``.pyasm``-file that is 
produced. Even easier, just to look in the test directory_ for files that end 
with ``.pyasm``.

In general, lines that start with "#" in column one are comments or code or function 
objects other than bytecode instructions.

Necessary fields that are in Python code object and function objects
are here. These include stuff like the Python "magic" number which
determines which Python bytecode opcodes to use and which Python
interpreter can be used to run the resulting program.

Module-level info
-----------------

Here is an example of the module-level information:

::

   # Python bytecode 2.2 (60717)
   # Timestamp in code: 1499156389 (2017-07-04 04:19:49)

The bytecode is necessary. However the timestamp is not. In Python 3
there is also a size modulo 2**32 that is recorded.

::

   # Source code size mod 2**32: 577 bytes

Method-level info
.................

Here is an example:

::

   # Method Name: gcd
   # Filename: exec
   # Argument count: 2
   # Kw-only arguments: 0
   # Number of locals: 2 # Stack size: 3
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
if they are, the instruction section can't refer to those values by list index value. (List index value is however used in the actual bytecode.)b

Although we haven't gotten to the exact format of instructions, what
the last sentence means is that

::

   LOAD_CONST 3

would be invalid if the size of the constant array is less than 4, or `constant[3]` wasn't defined by adding it to the `Constants` section. However when you put a value in parenthesis, that indicate a value rather than an index into a list. 
So you could instead write:

::

   LOAD_CONST (1)

which in this case does the same thing since `1 = constant[3]`. If the value 1 does not appear anywhere in the constants list, the assember would append the value 1 to the end of the list of the constants list. When writing the final bytecode file an appropriate constant index will be inserted into that instruction. 

Line Numbers and Labels
-----------------------

If the first token on a line is a number followed with a colon it is
taken as a line number to be applied to the next instruction. For
example

::

   66:
       LOAD_CONST ('this is line 66')

The ``LOAD_CONST`` instruction will be noted as being on line 66. Note
that Python requires that line numbers don't decrease as the a
method increases in bytecode offset. Also note that there can be white
space before the line number; the number doesn't have to be in
column 1.

Labels are like line numbers in that they have a colon suffix on the
line and must be the first thing on a line. However The first
character of a label _can't_ be a number: that's how we distinguish
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
exceptable and how operands are interpreted.

Instructions come after the other module or function information that starts with `#` and
is shown above.

An instruction then is something that is not a comment or code or
module field which would start with a #. And it is not a line number
or label listed in the last section. We've seen examples of
instructions above.

Instructions start with an opcode and will have an operand depending
on whether the opcode requires one or not. However as we've seen above
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

Possibly we should figure out when to put in ``EXTENDED_ARGS``
instructions. And for now, even though you put in ``EXTENDED_ARGS``,
the operand that follows may have the value folded into it. For
example in Python 3.6 where an operand can be at most 255, of you
wanted to jump relative 259 bytes you'd write:

::

   EXTENDED_ARG 1  # Needed because below offset is greater than 255 away
   JUMP_FORWARD 259  # Should really be 3 (= 259 - 256)

We should have a better API to generate instructions from inside
Python. This is pretty straightforward to do.

I've not put much in the way of error checking and error reporting.

.. _directory: https://github.com/rocky/python-xasm/tree/master/test
