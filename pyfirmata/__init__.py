from .boards import BOARDS
from .baudrate import BAUDRATE
from .pyfirmata import *  # NOQA
from serial.tools import list_ports

# TODO: should change above import to an explicit list, but people might rely on
# it, so do it in a backwards breaking release

__version__ = '1.1.3'  # Use bumpversion!

#Class to choose port automatically
class FindOptions():
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

		if ports is None: return None
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
	
	def FindLayout(self):
		baudrate_dict = BOARDS

		fmt = '+-------------+------------------+\n'
		fmt +='|    Option   |       Layout     |\n'
		fmt +='+-------------+------------------+\n'

		cont=1
		board__ = []
		for (board, dictBoard) in baudrate_dict.items():
			board__.append(dictBoard)
			x = self.centralize(cont, 13)
			y = self.centralize(board, 18)
#
			fmt +='|{0}|{1}|\n'.format(x, y)
			fmt +='+-------------+------------------+\n'
			cont+=1
		fmt+="Choose the layout of by the equivalent number: "
		
		layout__ = int(input(fmt))
		return board__[layout__-1]




# shortcut classes

class Arduino(Board):
	"""
	A board that will set itself up as a normal Arduino.
	"""
	def __init__(self, *args, **kwargs):
		port__ = FindOptions()
		
		if len(args) < 1 or args[0] is None:
			args = []
			args.append(port__.chooseport())
		else:
			args = list(args)
		##add board
		layout = port__.FindLayout()
		args.append(layout)
		
		##add baudrate
		baudrate=port__.baudrate()
		args.append(baudrate)

		super(Arduino, self).__init__(*args, **kwargs)

	def __str__(self):
		return "Arduino {0.name} on {0.sp.port}".format(self)
