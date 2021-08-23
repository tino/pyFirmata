#!/usr/bin/python3

from setuptools import setup

with open('README_py.rst') as f:
    long_description = f.read()

setup(
    name='pyFirmata2',
    version='2.2.0',
    description="Use your Arduino as a data acquisition card under Python",
    long_description=long_description,
    author='Bernd Porr',
    author_email='mail@berndporr.me.uk',
    packages=['pyfirmata2'],
    include_package_data=True,
    install_requires=['pyserial'],
    zip_safe=False,
    url='https://github.com/berndporr/pyFirmata2',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
)
