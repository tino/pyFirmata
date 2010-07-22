#!/usr/bin/env python
 
from distutils.core import setup

setup(
    name='pyFirmata',
    version='0.9',
    description="A Python interface for the Firmata procotol",
    author='Tino de Bruijn',
    author_email='tinodb@gmail.com',
    packages=['pyfirmata'],
    include_package_data=True,
    zip_safe=False,
)