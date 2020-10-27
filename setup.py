#!/usr/bin/env python

"""Setup script for the 'xasm' distribution."""

from __pkginfo__ import (
    author,
    author_email,
    license,
    long_description,
    classifiers,
    modname,
    py_modules,
    setup_requires,
    short_desc,
    tests_require,
    __version__,
    web,
    zip_safe,
)

from setuptools import setup, find_packages

setup(
    author=author,
    author_email=author_email,
    classifiers=classifiers,
    description=short_desc,
    license=license,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    name=modname,
    packages=find_packages(),
    py_modules=py_modules,
    setup_requires=setup_requires,
    entry_points="""
        [console_scripts]
        pyc-xasm    = xasm.xasm_cli:main
        pyc-convert = xasm.pyc_convert:main
       """,
    tests_require=tests_require,
    url=web,
    version=__version__,
    zip_safe=zip_safe,
)
