import serial
import serial.tools.list_ports

l = serial.tools.list_ports.comports()
print(l)
for ll in l:
    print(ll.description)
