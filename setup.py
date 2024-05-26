#!/usr/bin/env python

"""Setup script for the 'xasm' distribution."""

from setuptools import find_packages, setup

from __pkginfo__ import (__version__, author, author_email, classifiers,
                         install_requires, license, long_description, modname,
                         py_modules, short_desc, tests_require, web, zip_safe)

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
    install_requires=install_requires,
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
