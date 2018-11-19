#!/usr/bin/python3

from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='pyFirmata2',
    version='1.0.0',
    description="Use your Arduino as a data acquisition card",
    long_description=long_description,
    author='Bernd Porr',
    author_email='mail@berndporr.me.uk',
    packages=['pyfirmata2'],
    include_package_data=True,
    install_requires=['pyserial'],
    zip_safe=False,
    url='https://github.com/berndporr/pyFirmata2',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
    ],
)
