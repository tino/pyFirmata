from .boards import BOARDS
from .pyfirmata import *  # NOQA
from serial.tools import list_ports

# TODO: should change above import to an explicit list, but people might rely on
# it, so do it in a backwards breaking release

__version__ = '1.1.3'  # Use bumpversion!

#Class to choose port automatically
class FindPort():
	## list ports
	def port_(self):
		list = []
		for poert in list_ports.comports():
			list.append(poert.device)
		return list
		
	#Choose port
	def chooseport(self):
		ports = self.port_()
		if len(ports) > 1:
			cont = 0
			g="----------------\n"
			for porta in ports:
				g+=f"{cont+1}. {porta}\n"
				cont+=1
			g+="----------------"
			print(g)
			choose = int(input("Choose the port by entering the equivalent number: "))
			return ports[choose-1]
		else:
			return ports[0]

# shortcut classes

class Arduino(Board):
	"""
	A board that will set itself up as a normal Arduino.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			porta = FindPort()
			args = []
			args.append(porta.chooseport())
		else:
			args = list(args)
	
		args.append(BOARDS['arduino'])
		super(Arduino, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino {0.name} on {0.sp.port}".format(self)


class ArduinoMega(Board):
	"""
	A board that will set itself up as an Arduino Mega.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			porta = FindPort()
			args = []
			args.append(porta.chooseport())
		else:
			args = list(args)
		args.append(BOARDS['arduino_mega'])
		super(ArduinoMega, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino Mega {0.name} on {0.sp.port}".format(self)


class ArduinoDue(Board):
	"""
	A board that will set itself up as an Arduino Due.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			porta = FindPort()
			args = []
			args.append(porta.chooseport())
		else:
			args = list(args)
		args.append(BOARDS['arduino_due'])
		super(ArduinoDue, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino Due {0.name} on {0.sp.port}".format(self)


class ArduinoNano(Board):
	"""
	A board that will set itself up as an Arduino Nano.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			porta = FindPort()
			args = []
			args.append(porta.chooseport())
		else:
			args = list(args)
		args.append(BOARDS['arduino_nano'])
		super(ArduinoNano, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino Nano {0.name} on {0.sp.port}".format(self)

class ArduinoLeonardo(Board):
	"""
	A board that will set itself up as an Arduino Leonardo.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			porta = FindPort()
			args = []
			args.append(porta.chooseport())
		else:
			args = list(args)
		args.append(BOARDS['arduino_leonardo'])
		super(ArduinoLeonardo, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino Leonardo {0.name} on {0.sp.port}".format(self)
