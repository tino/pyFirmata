#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Example of usage of the "ping" method of Ping to calculate distances.

For this example to work plug an HC-SR04 ultrasonic ranging sensor
into the pin 8 (trigger and echo pins on the sensor conected to pin 8)
as shown in the :file:`ping.png` diagram
(note: image from https://github.com/rwaldron/johnny-five/wiki/proximity
 Copyright (c) 2016 The Johnny-Five Contributors).
"""
__author__      = "Borja López Soilán <neopolus@kami.es>"

import time
import sys
sys.path.insert(0, '../') # We want to import the local pyfirmata
from pyfirmata import Arduino, util

board = util.get_the_board(identifier='ttyACM', timeout=10)
with board:
	echo_pin = board.get_pin('d:8:o')
	while True: 

 		# Send a ping and get the echo time:
	    duration = echo_pin.ping()

	    if duration:
	    	# Normal distance (speed of sound based)
	    	distance = util.ping_time_to_distance(duration)

	    	# Distance based on calibration points.
	    	calibration = [(680.0, 10.0), (1460.0, 20.0), (2210.0, 30.0)]
	    	cal_distance = util.ping_time_to_distance(duration, calibration)

	    	print "Distance: \t%scm \t%scm (calibrated) \t(%ss)" \
	    				% (distance, cal_distance, duration)
	    else:
	    	print "No distance!"

	    time.sleep(0.2)