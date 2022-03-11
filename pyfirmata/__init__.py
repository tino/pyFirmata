from .boards import BOARDS
from .baudrate import BAUDRATE
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
		if len(list) > 0:
			return list
		return None
		
	#Choose port
	def chooseport(self):
		ports = self.port_()
		if len(ports) > 1:
			cont = 0
			g="----------------\n"
			for port__ in ports:
				g+=f"{cont+1}. {port__}\n"
				cont+=1
			g+="----------------"
			print(g)
			choose = int(input("Choose the port by entering the equivalent number: "))
			return ports[choose-1]

		return ports[0]
	
	def centralize(self, value, default:int=10, character:str=None):
		string = str(value)
		diff = abs(default - len(string))
		character = ' ' if character is None else character

		if diff > 0:
			if diff%2 == 0: 
				diff/=2; diff=int(diff)
				string = string + character*diff
				string = character*diff + string
			else:
				diff/=2; diff=int(diff)
				string = string + character*(diff+1)
				string = character*diff + string

		return string

	def baudrate(self):
		baudrate_dict = BAUDRATE['velocity']

		fmt = '+----------+----------+\n'
		fmt +='|  Option  | baudrate |\n'
		fmt +='+----------+----------+\n'
		for (option, rate) in baudrate_dict.items():
			x = self.centralize(option, 10)
			y = self.centralize(rate, 10)

			fmt +='|{0}|{1}|\n'.format(x, y)
			fmt +='+----------+----------+\n'

		fmt+="Choose the baudrate of by the equivalent number: "
		baudrate__ = input(fmt)

		if baudrate__ not in BAUDRATE['velocity']: return 57600

		return BAUDRATE['velocity'][str(baudrate__)]

# shortcut classes

class Arduino(Board):
	"""
	A board that will set itself up as a normal Arduino.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			port__ = FindPort()
			args = []
			args.append(port__.chooseport())
		else:
			args = list(args)

		##add board
		args.append(BOARDS['arduino'])
		
		##add baudrate
		baudrate=port__.baudrate()
		args.append(baudrate)

		super(Arduino, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino {0.name} on {0.sp.port}".format(self)


class ArduinoMega(Board):
	"""
	A board that will set itself up as an Arduino Mega.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			port__ = FindPort()
			args = []
			args.append(port__.chooseport())
		else:
			args = list(args)
		args.append(BOARDS['arduino_mega'])

		baudrate=port__.baudrate()
		args.append(baudrate)

		super(ArduinoMega, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino Mega {0.name} on {0.sp.port}".format(self)


class ArduinoDue(Board):
	"""
	A board that will set itself up as an Arduino Due.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			port__ = FindPort()
			args = []
			args.append(port__.chooseport())
		else:
			args = list(args)

		args.append(BOARDS['arduino_due'])

		baudrate=port__.baudrate()
		args.append(baudrate)

		super(ArduinoDue, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino Due {0.name} on {0.sp.port}".format(self)


class ArduinoNano(Board):
	"""
	A board that will set itself up as an Arduino Nano.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			port__ = FindPort()
			args = []
			args.append(port__.chooseport())
		else:
			args = list(args)
		
		args.append(BOARDS['arduino_nano'])
		
		baudrate=port__.baudrate()
		args.append(baudrate)

		super(ArduinoNano, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino Nano {0.name} on {0.sp.port}".format(self)

class ArduinoLeonardo(Board):
	"""
	A board that will set itself up as an Arduino Leonardo.
	"""
	def __init__(self, *args, **kwargs):
		if len(args) < 1 or args[0] is None:
			port__ = FindPort()
			args = []
			args.append(port__.chooseport())
		else:
			args = list(args)

		args.append(BOARDS['arduino_leonardo'])

		baudrate=port__.baudrate()
		args.append(baudrate)

		super(ArduinoLeonardo, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino Leonardo {0.name} on {0.sp.port}".format(self)
