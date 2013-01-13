#!/usr/bin/env python

from distutils.core import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='pyFirmata',
    version='0.9.5',  # Don't forget to change pyfirmata.__version__!
    description="A Python interface for the Firmata procotol",
    long_description=long_description,
    author='Tino de Bruijn',
    author_email='tinodb@gmail.com',
    packages=['pyfirmata'],
    include_package_data=True,
    install_requires=['pyserial'],
    zip_safe=False,
    url='https://github.com/tino/pyFirmata',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
        'Topic :: Home Automation',
    ],
)
