"""xasm packaging information"""

# To the extent possible we make this file look more like a
# configuration file rather than code like setup.py. I find putting
# configuration stuff in the middle of a function call in setup.py,
# which for example requires commas in between parameters, is a little
# less elegant than having it here with reduced code, albeit there
# still is some room for improvement.

# Things that change more often go here.
copyright = """
Copyright (C) 2017, 2019-2020 Rocky Bernstein <rb@dustyfeet.com>.
"""

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Topic :: Software Development :: Debuggers",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

_six = "six >= 1.10.0"

# The rest in alphabetic order
author = "Rocky Bernstein"
author_email = "rb@dustyfeet.com"
ftp_url = None
install_requires = [_six]
license = "GPL-2.0"
mailing_list = "python-debugger@googlegroups.com"
modname = "xasm"
py_modules = None
setup_requires = ["pytest-runner", "xdis >= 5.0.0, < 5.1.0"]
# scripts            = ['bin/pydisasm']
short_desc = "Python cross-version byte-code assembler"
tests_require = ["pytest", _six]
web = "https://github.com/rocky/python-xasm/"

# tracebacks in zip files are funky and not debuggable
zip_safe = True

import os.path as osp


def get_srcdir():
    filename = osp.normcase(osp.dirname(osp.abspath(__file__)))
    return osp.realpath(filename)


srcdir = get_srcdir()


def read(*rnames):
    return open(osp.join(srcdir, *rnames)).read()


# Get info from files; set: long_description and VERSION
long_description = read("README.rst") + "\n"
exec(read("xasm/version.py"))
