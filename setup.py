#!/usr/bin/env python
 
from distutils.core import setup

import pyfirmata

setup(
    name='pyFirmata',
    version=pyfirmata.__version__,
    description="A Python interface for the Firmata procotol",
    author='Tino de Bruijn',
    author_email='tinodb@gmail.com',
    packages=['pyfirmata'],
    include_package_data=True,
    zip_safe=False,
)