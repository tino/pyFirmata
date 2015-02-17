#!/usr/bin/env python

from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='pyFirmata',
    version='1.0.2',  # Use bumpversion!
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
        'Topic :: Home Automation',
    ],
)
