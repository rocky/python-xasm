1.2.2 2025-10-13
----------------

* Pass PyPy status to write_pyc.
* Correct packaging pyc-xasm command-line entry.

1.2.1 2025-10-13
----------------

* Repackage for Python 3.11 and poetry. I can't describe what thrill it gives me to have to do this every few years.
* Correct bug respecting `create_code` API Fixes #24
* More explicit comments. Add some `##` comments. Document module and method information better.
* `decode_linotab()` is now `decode_lineno_tab_old` to make it clear that this routine works for version before 3.10.
* Avoid using `asm.code.to_native()` for now, since there are bugs.
* Handle numeric labels better.
* Adjust field name `co_linetable` for bytecode after 3.10.
* Warn if duplicate line numbers seen and the assembler is before bytecode for 3.10
* Improve `EXTENDED_ARG` handling and creation.
* If Python bytecode is not set, complain and exit.
* Detect and handle line numbers on instructions
* Add a check for last instruction being either a `RETURN_VALUE`, or `RERAISE`, or `RAISE_VARARGS`
* Offsets in bytecode for 3.10 need to be divided by two
* Lint code a little

1.2.0 2021-11-07
----------------

* Adjust to use xdis 6.0.3 or later
* start adding `.READ` directive

1.1.1 2020-10-27
----------------

- Fix bugs in cross-assembly bytecode writing
- Detect PyPy.
- Add SIP hash field. Fixes #4

1.1.0 2020-04-24
----------------

- Fix bugs in writing 3.7 and 3.8 pyc
- Require newer xdis to get fixes to 3.8 pyc marshaling


1.0.0 2019-10-19
----------------

- Go over docs.
- Require newer xdis to get early bytecodes bytecodes: 1.0, 1.1, 1.2, and 1.6.
- More sensitive to network ordering
