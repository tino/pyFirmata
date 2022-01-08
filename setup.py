#!/usr/bin/env python

from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='arduPython',
    version='1.1.3',  # Use bumpversion!
    description="A Python interface for the Firmata procotol",
    long_description=long_description,
    author='Francisco Iago Lira Passos',
    author_email='iagolirapassosb@gmail.com',
    packages=['pyfirmata'],
    include_package_data=True,
    install_requires=['pyserial'],
    zip_safe=False,
    url='https://github.com/BosonsHiggs/arduPython',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',        
        'Topic :: Utilities',
        'Topic :: Home Automation',
    ],
)
