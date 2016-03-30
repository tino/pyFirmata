#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Example of usage of the "with" statement with the board to read a pin.
"""
__author__      = "Borja López Soilán <neopolus@kami.es>"

import time
import sys
sys.path.insert(0, '../') # We want to import the local pyfirmata
from pyfirmata import Arduino, util

board = util.get_the_board(identifier='ttyACM', timeout=10)
with board:
	input_pin = board.get_pin('d:8:i')
	while True:
		value = input_pin.read()
		print "input_pin = %s" % value
		time.sleep(1)
